package tech.gandiva.sonicwall.wire;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import tech.gandiva.sonicwall.model.AddressObject;
import tech.gandiva.sonicwall.model.AddressObjectType;

class AddressObjectWireTest {

  @Test
  void roundTripsHostObject() {
    AddressObject original =
        new AddressObject()
            .name("srv")
            .zone("LAN")
            .type(AddressObjectType.HOST)
            .host("10.0.0.5");
    AddressObject parsed = AddressObjectWire.fromWire(AddressObjectWire.toEnvelope(original).addressObject.ipv4);
    assertEquals("srv", parsed.name());
    assertEquals(AddressObjectType.HOST, parsed.type());
    assertEquals("10.0.0.5", parsed.host());
  }

  @Test
  void roundTripsNetworkObject() {
    AddressObject original =
        new AddressObject()
            .name("net")
            .zone("LAN")
            .type(AddressObjectType.NETWORK)
            .network("10.0.0.0/24");
    AddressObject parsed = AddressObjectWire.fromWire(AddressObjectWire.toEnvelope(original).addressObject.ipv4);
    assertEquals(AddressObjectType.NETWORK, parsed.type());
    assertEquals("10.0.0.0/24", parsed.network());
  }

  @Test
  void roundTripsRangeFqdnAndMac() {
    AddressObject range =
        new AddressObject()
            .name("r")
            .zone("LAN")
            .type(AddressObjectType.RANGE)
            .rangeStart("10.0.0.1")
            .rangeEnd("10.0.0.10");
    assertEquals("10.0.0.1", AddressObjectWire.fromWire(AddressObjectWire.toEnvelope(range).addressObject.ipv4).rangeStart());

    AddressObject fqdn =
        new AddressObject().name("f").zone("WAN").type(AddressObjectType.FQDN).fqdn("example.com");
    assertEquals("example.com", AddressObjectWire.fromWire(AddressObjectWire.toEnvelope(fqdn).addressObject.ipv4).fqdn());

    AddressObject mac =
        new AddressObject().name("m").zone("LAN").type(AddressObjectType.MAC).mac("00:11:22:33:44:55");
    assertEquals("00:11:22:33:44:55", AddressObjectWire.fromWire(AddressObjectWire.toEnvelope(mac).addressObject.ipv4).mac());
  }

  @Test
  void parsesNetworkMaskToCidr() {
    AddressObjectWire wire = new AddressObjectWire();
    wire.name = "n";
    wire.zone = "LAN";
    wire.network = new AddressObjectWire.NetworkWire();
    wire.network.subnet = "172.16.0.0";
    wire.network.mask = "255.255.0.0";
    assertEquals("172.16.0.0/16", AddressObjectWire.fromWire(wire).network());
  }
}
