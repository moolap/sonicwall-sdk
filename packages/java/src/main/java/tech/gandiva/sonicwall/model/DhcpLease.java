package tech.gandiva.sonicwall.model;

public record DhcpLease(String ip, String mac, String hostname, String expires, String iface) {}
