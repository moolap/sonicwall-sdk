package tech.gandiva.sonicwall.model;

public record NatPolicy(
    String name,
    boolean enabled,
    String inboundInterface,
    String outboundInterface,
    String originalSource,
    String translatedSource,
    String originalDestination,
    String translatedDestination,
    String originalService,
    String translatedService,
    String comment) {}
