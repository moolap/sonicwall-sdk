package tech.gandiva.sonicwall.model;

public record ServiceProtocol(PortRange tcp, PortRange udp, IcmpSpec icmp) {
  public static ServiceProtocol empty() {
    return new ServiceProtocol(null, null, null);
  }
}
