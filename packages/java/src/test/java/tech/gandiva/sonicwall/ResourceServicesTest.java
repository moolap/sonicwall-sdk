package tech.gandiva.sonicwall;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.get;
import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.apiPath;
import static tech.gandiva.sonicwall.support.SonicWallTestSupport.okStatus;

import com.github.tomakehurst.wiremock.junit5.WireMockRuntimeInfo;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import tech.gandiva.sonicwall.model.AccessRule;
import tech.gandiva.sonicwall.model.DhcpLease;
import tech.gandiva.sonicwall.model.NatPolicy;
import tech.gandiva.sonicwall.model.NetworkInterface;
import tech.gandiva.sonicwall.model.ServiceObject;
import tech.gandiva.sonicwall.support.SonicWallTestSupport;

@WireMockTest
class ResourceServicesTest {
  private SonicWallClient client;

  @BeforeEach
  void setUp(WireMockRuntimeInfo wm) {
    client = SonicWallTestSupport.connectedClient(wm);
  }

  @Test
  void accessRulesList(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/access-rules/ipv4")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "access_rules": [
                            {"access_rule": {"ipv4": {"name": "rule1", "from": "LAN", "to": "WAN", "action": "allow", "enabled": true}}}
                          ]
                        }
                        """)));

    var rules = client.accessRules.list();
    assertEquals(1, rules.size());
    AccessRule rule = rules.get(0);
    assertEquals("rule1", rule.name());
    assertEquals("LAN", rule.fromZone());
    assertEquals("WAN", rule.toZone());
    assertEquals("allow", rule.action());
    assertTrue(rule.enabled());
  }

  @Test
  void natPoliciesList(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/nat-policies/ipv4")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "nat_policies": [
                            {"nat_policy": {"ipv4": {"name": "nat1", "comment": "lab"}}}
                          ]
                        }
                        """)));

    var policies = client.natPolicies.list();
    assertEquals(1, policies.size());
    NatPolicy nat = policies.get(0);
    assertEquals("nat1", nat.name());
    assertEquals("lab", nat.comment());
  }

  @Test
  void serviceObjectsList(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/service-objects")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "service_objects": [
                            {"service_object": {"name": "HTTP", "protocol": {"tcp": {"begin": 80, "end": 80}}}}
                          ]
                        }
                        """)));

    var objects = client.serviceObjects.list();
    assertEquals(1, objects.size());
    ServiceObject svc = objects.get(0);
    assertEquals("HTTP", svc.name());
    assertEquals(80, svc.protocol().tcp().begin());
  }

  @Test
  void interfacesListAndGet(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/interfaces")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "interfaces": [
                            {"name": "X0", "zone": "LAN", "ip": "192.168.1.1"}
                          ]
                        }
                        """)));
    stubFor(
        get(urlEqualTo(apiPath("/interfaces/name/X0")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "name": "X0", "zone": "LAN", "ip": "192.168.1.1"
                        }
                        """)));

    assertEquals(1, client.interfaces.list().size());
    NetworkInterface iface = client.interfaces.get("X0");
    assertEquals("X0", iface.name());
    assertEquals("LAN", iface.zone());
  }

  @Test
  void dhcpListLeases(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/dhcp/server/lease")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "dhcp_server_leases": [
                            {"ip": "192.168.1.50", "mac": "aa:bb:cc:dd:ee:ff", "hostname": "pc1"}
                          ]
                        }
                        """)));

    var leases = client.dhcp.listLeases();
    assertEquals(1, leases.size());
    DhcpLease lease = leases.get(0);
    assertEquals("192.168.1.50", lease.ip());
    assertEquals("pc1", lease.hostname());
  }

  @Test
  void emptyCollectionsReturnEmptyLists(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/access-rules/ipv4")))
            .willReturn(aResponse().withStatus(200).withBody(okStatus())));
    assertTrue(client.accessRules.list().isEmpty());
  }

  @Test
  void accessRulesListIgnoresMalformedItems(WireMockRuntimeInfo wm) {
    stubFor(
        get(urlEqualTo(apiPath("/access-rules/ipv4")))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withBody(
                        """
                        {
                          "status": {"success": true, "info": []},
                          "access_rules": [123, {"access_rule": {"ipv4": {"name": "ok", "from": "A", "to": "B", "action": "allow"}}}]
                        }
                        """)));
    assertEquals(1, client.accessRules.list().size());
    assertFalse(client.accessRules.list().isEmpty());
  }
}
