package tech.gandiva.sonicwall.model;

public record NetworkInterface(
    String name,
    String ipAssignment,
    String ip,
    String subnet,
    String zone,
    boolean enabled,
    String comment) {}
