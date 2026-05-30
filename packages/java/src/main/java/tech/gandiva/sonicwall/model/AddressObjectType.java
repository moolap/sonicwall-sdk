package tech.gandiva.sonicwall.model;

/** IPv4 address object type. */
public enum AddressObjectType {
  HOST("host"),
  NETWORK("network"),
  RANGE("range"),
  FQDN("fqdn"),
  MAC("mac");

  private final String wireValue;

  AddressObjectType(String wireValue) {
    this.wireValue = wireValue;
  }

  public String wireValue() {
    return wireValue;
  }
}
