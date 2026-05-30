package tech.gandiva.sonicwall.wire;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import tech.gandiva.sonicwall.model.AddressObject;
import tech.gandiva.sonicwall.model.AddressObjectType;

@JsonIgnoreProperties(ignoreUnknown = true)
public final class AddressObjectWire {
  public String name;
  public String zone;
  public HostWire host;
  public NetworkWire network;
  public RangeWire range;
  public FqdnWire fqdn;
  public MacWire mac;

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class HostWire {
    public String ip;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class NetworkWire {
    public String subnet;
    public String mask;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class RangeWire {
    public String begin;
    public String end;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class FqdnWire {
    public String domain;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class MacWire {
    public String address;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class Envelope {
    @JsonProperty("address_object")
    public AddressObjectContainer addressObject;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class AddressObjectContainer {
    public AddressObjectWire ipv4;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class ListResponse {
    @JsonProperty("address_objects")
    public List<Envelope> addressObjects;
  }

  public static AddressObject fromWire(AddressObjectWire wire) {
    AddressObject obj = new AddressObject().name(wire.name).zone(wire.zone);
    if (wire.host != null && wire.host.ip != null) {
      return obj.type(AddressObjectType.HOST).host(wire.host.ip);
    }
    if (wire.network != null && wire.network.subnet != null) {
      int prefix = maskToPrefix(wire.network.mask);
      return obj.type(AddressObjectType.NETWORK).network(wire.network.subnet + "/" + prefix);
    }
    if (wire.range != null) {
      return obj.type(AddressObjectType.RANGE).rangeStart(wire.range.begin).rangeEnd(wire.range.end);
    }
    if (wire.fqdn != null && wire.fqdn.domain != null) {
      return obj.type(AddressObjectType.FQDN).fqdn(wire.fqdn.domain);
    }
    if (wire.mac != null && wire.mac.address != null) {
      return obj.type(AddressObjectType.MAC).mac(wire.mac.address);
    }
    return obj;
  }

  public static Envelope toEnvelope(AddressObject obj) {
    AddressObjectWire wire = new AddressObjectWire();
    wire.name = obj.name();
    wire.zone = obj.zone();
    switch (obj.type()) {
      case HOST -> {
        wire.host = new HostWire();
        wire.host.ip = obj.host();
      }
      case NETWORK -> {
        wire.network = new NetworkWire();
        String[] parts = splitCidr(obj.network());
        wire.network.subnet = parts[0];
        wire.network.mask = prefixToMask(Integer.parseInt(parts[1]));
      }
      case RANGE -> {
        wire.range = new RangeWire();
        wire.range.begin = obj.rangeStart();
        wire.range.end = obj.rangeEnd();
      }
      case FQDN -> {
        wire.fqdn = new FqdnWire();
        wire.fqdn.domain = obj.fqdn();
      }
      case MAC -> {
        wire.mac = new MacWire();
        wire.mac.address = obj.mac();
      }
      default -> {}
    }
    Envelope env = new Envelope();
    env.addressObject = new AddressObjectContainer();
    env.addressObject.ipv4 = wire;
    return env;
  }

  private static String[] splitCidr(String cidr) {
    int slash = cidr.indexOf('/');
    if (slash < 0) {
      return new String[] {cidr, "32"};
    }
    return new String[] {cidr.substring(0, slash), cidr.substring(slash + 1)};
  }

  private static int maskToPrefix(String mask) {
    if (mask == null || mask.isBlank()) {
      return 32;
    }
    String[] octets = mask.split("\\.");
    int bits = 0;
    for (String octet : octets) {
      int value = Integer.parseInt(octet);
      bits += Integer.bitCount(value);
    }
    return bits;
  }

  private static String prefixToMask(int prefix) {
    if (prefix <= 0) {
      return "0.0.0.0";
    }
    long mask = (0xFFFFFFFFL << (32 - prefix)) & 0xFFFFFFFFL;
    return ((mask >> 24) & 0xff) + "." + ((mask >> 16) & 0xff) + "." + ((mask >> 8) & 0xff) + "." + (mask & 0xff);
  }
}
