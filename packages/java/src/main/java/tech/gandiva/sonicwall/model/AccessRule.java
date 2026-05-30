package tech.gandiva.sonicwall.model;

public record AccessRule(
    String name,
    String fromZone,
    String toZone,
    String action,
    boolean enabled,
    boolean log,
    RulePriority priority,
    RuleAddress sourceAddress,
    RuleAddress destinationAddress,
    RuleService service,
    String comment) {}
