package tech.gandiva.sonicwall.model;

/** SonicOS IPv4 address object. */
public final class AddressObject {
  private String name;
  private String zone;
  private AddressObjectType type;
  private String host;
  private String network;
  private String rangeStart;
  private String rangeEnd;
  private String fqdn;
  private String mac;

  public String name() {
    return name;
  }

  public AddressObject name(String name) {
    this.name = name;
    return this;
  }

  public String zone() {
    return zone;
  }

  public AddressObject zone(String zone) {
    this.zone = zone;
    return this;
  }

  public AddressObjectType type() {
    return type;
  }

  public AddressObject type(AddressObjectType type) {
    this.type = type;
    return this;
  }

  public String host() {
    return host;
  }

  public AddressObject host(String host) {
    this.host = host;
    return this;
  }

  public String network() {
    return network;
  }

  public AddressObject network(String network) {
    this.network = network;
    return this;
  }

  public String rangeStart() {
    return rangeStart;
  }

  public AddressObject rangeStart(String rangeStart) {
    this.rangeStart = rangeStart;
    return this;
  }

  public String rangeEnd() {
    return rangeEnd;
  }

  public AddressObject rangeEnd(String rangeEnd) {
    this.rangeEnd = rangeEnd;
    return this;
  }

  public String fqdn() {
    return fqdn;
  }

  public AddressObject fqdn(String fqdn) {
    this.fqdn = fqdn;
    return this;
  }

  public String mac() {
    return mac;
  }

  public AddressObject mac(String mac) {
    this.mac = mac;
    return this;
  }
}
