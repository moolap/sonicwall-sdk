package tech.gandiva.sonicwall;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.containing;
import static com.github.tomakehurst.wiremock.client.WireMock.get;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.put;
import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.apiPath;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.okStatus;

import com.github.tomakehurst.wiremock.junit5.WireMockRuntimeInfo;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import tech.gandiva.sonicwall.exception.ConflictException;
import tech.gandiva.sonicwall.exception.NotFoundException;
import tech.gandiva.sonicwall.model.AddressObject;
import tech.gandiva.sonicwall.model.AddressObjectType;
import tech.gandiva.sonicwall.support.SonicWallTestSupport;

@WireMockTest
class AddressObjectsExtendedTest {
  private SonicWallClient client;

  @BeforeEach
  void setUp(WireMockRuntimeInfo wm) {
    client = SonicWallTestSupport.connectedClient(wm);
  }

  @Test
  void listReturnsEmptyWhenCollectionMissing(WireMockRuntimeInfo wm) {
    stubFor(get(urlEqualTo(apiPath("/address-objects/ipv4"))).willReturn(aResponse().withStatus(200).withBody(okStatus())));
    assertTrue(client.addressObjects.list().isEmpty());
  }

  @Test
  void createRetriesWithArrayPayloadOnSchemaError(WireMockRuntimeInfo wm) {
    stubFor(
        post(urlEqualTo(apiPath("/address-objects/ipv4")))
            .inScenario("schema")
            .whenScenarioStateIs("Started")
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {"status":{"success":false,"info":[{"code":400,"message":"Schema validation error for address_objects"}]}}
                        """))
            .willSetStateTo("Retried"));
    stubFor(
        post(urlEqualTo(apiPath("/address-objects/ipv4")))
            .inScenario("schema")
            .whenScenarioStateIs("Retried")
            .withRequestBody(containing("\"address_objects\""))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4/name/array-host")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "address_object": {"ipv4": {"name": "array-host", "zone": "LAN", "host": {"ip": "10.0.0.8"}}}
                        }
                        """)));

    AddressObject created =
        client.addressObjects.create(
            new AddressObject()
                .name("array-host")
                .zone("LAN")
                .type(AddressObjectType.HOST)
                .host("10.0.0.8"));
    assertEquals("array-host", created.name());
  }

  @Test
  void createSurfacesConflict(WireMockRuntimeInfo wm) {
    stubFor(
        post(urlEqualTo(apiPath("/address-objects/ipv4")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {"status":{"success":false,"info":[{"code":1055,"message":"Object already exists"}]}}
                        """)));
    assertThrows(
        ConflictException.class,
        () ->
            client.addressObjects.create(
                new AddressObject()
                    .name("dup")
                    .zone("LAN")
                    .type(AddressObjectType.HOST)
                    .host("10.0.0.1")));
  }

  @Test
  void ensureUpdatesExistingObject(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4/name/existing")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "address_object": {"ipv4": {"name": "existing", "zone": "LAN", "host": {"ip": "10.0.0.1"}}}
                        }
                        """)));
    stubFor(
        put(urlEqualTo(apiPath("/address-objects/ipv4/name/existing")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));

    var result =
        client.addressObjects.ensure(
            new AddressObject()
                .name("existing")
                .zone("LAN")
                .type(AddressObjectType.HOST)
                .host("10.0.0.2"));
    assertFalse(result.created());
    assertEquals("existing", result.object().name());
  }

  @Test
  void getEncodesObjectName(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4/name/space%20name")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "address_object": {"ipv4": {"name": "space name", "zone": "LAN", "host": {"ip": "10.0.0.3"}}}
                        }
                        """)));

    AddressObject obj = client.addressObjects.get("space name");
    assertEquals("space name", obj.name());
  }

  @Test
  void sessionExpiryTriggersReauth(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4")))
            .inScenario("reauth")
            .whenScenarioStateIs("Started")
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {"status":{"success":false,"info":[{"code":1085,"message":"Session expired"}]}}
                        """))
            .willSetStateTo("Expired"));
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4")))
            .inScenario("reauth")
            .whenScenarioStateIs("Expired")
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "address_objects": []
                        }
                        """)));

    assertTrue(client.addressObjects.list().isEmpty());
  }

  @Test
  void getThrowsNotFoundForMissingObject(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4/name/ghost")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody("{\"status\":{\"success\":true,\"info\":[]},\"address_objects\":[]}")));
    assertThrows(NotFoundException.class, () -> client.addressObjects.get("ghost"));
  }
}
