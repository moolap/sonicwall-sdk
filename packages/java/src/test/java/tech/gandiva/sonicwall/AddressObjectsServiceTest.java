package tech.gandiva.sonicwall;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.delete;
import static com.github.tomakehurst.wiremock.client.WireMock.get;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.put;
import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.apiPath;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.okStatus;

import com.github.tomakehurst.wiremock.junit5.WireMockRuntimeInfo;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import tech.gandiva.sonicwall.model.AddressObject;
import tech.gandiva.sonicwall.model.AddressObjectType;
import tech.gandiva.sonicwall.support.SonicWallTestSupport;

@WireMockTest
class AddressObjectsServiceTest {
  private SonicWallClient client;

  @BeforeEach
  void setUp(WireMockRuntimeInfo wm) {
    client = SonicWallTestSupport.connectedClient(wm);
  }

  @Test
  void listReturnsAddressObjects(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "address_objects": [
                            {"address_object": {"ipv4": {"name": "my-server", "zone": "LAN", "host": {"ip": "10.0.0.100"}}}},
                            {"address_object": {"ipv4": {"name": "internal-net", "zone": "LAN", "network": {"subnet": "10.0.0.0", "mask": "255.255.255.0"}}}}
                          ]
                        }
                        """)));

    var objects = client.addressObjects.list();
    assertEquals(2, objects.size());
    assertEquals("my-server", objects.get(0).name());
    assertEquals(AddressObjectType.HOST, objects.get(0).type());
    assertEquals("10.0.0.100", objects.get(0).host());
    assertEquals("internal-net", objects.get(1).name());
    assertEquals(AddressObjectType.NETWORK, objects.get(1).type());
  }

  @Test
  void createAndDeleteObject(WireMockRuntimeInfo wm) {
    stubFor(
        post(urlEqualTo(apiPath("/address-objects/ipv4")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4/name/new-host")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "address_object": {"ipv4": {"name": "new-host", "zone": "LAN", "host": {"ip": "10.0.0.50"}}}
                        }
                        """)));
    stubFor(
        delete(urlEqualTo(apiPath("/address-objects/ipv4/name/new-host")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));

    AddressObject created =
        client.addressObjects.create(
            new AddressObject()
                .name("new-host")
                .zone("LAN")
                .type(AddressObjectType.HOST)
                .host("10.0.0.50"));
    assertEquals("new-host", created.name());
    client.addressObjects.delete("new-host");
  }

  @Test
  void ensureCreatesWhenMissing(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4/name/upsert-me")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody("{\"status\":{\"success\":true,\"info\":[]},\"address_objects\":[]}")));
    stubFor(
        post(urlEqualTo(apiPath("/address-objects/ipv4")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));

    var result =
        client.addressObjects.ensure(
            new AddressObject()
                .name("upsert-me")
                .zone("LAN")
                .type(AddressObjectType.HOST)
                .host("10.0.0.99"));
    assertTrue(result.created());
    assertEquals("upsert-me", result.object().name());
  }

  @Test
  void updateExistingObject(WireMockRuntimeInfo wm) {
    stubFor(
        put(urlEqualTo(apiPath("/address-objects/ipv4/name/my-server")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));
    stubFor(
        get(urlEqualTo(apiPath("/address-objects/ipv4/name/my-server")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "address_object": {"ipv4": {"name": "my-server", "zone": "LAN", "host": {"ip": "10.0.0.200"}}}
                        }
                        """)));

    AddressObject updated =
        client.addressObjects.update(
            "my-server",
            new AddressObject()
                .name("my-server")
                .zone("LAN")
                .type(AddressObjectType.HOST)
                .host("10.0.0.200"));
    assertEquals("10.0.0.200", updated.host());
  }
}
