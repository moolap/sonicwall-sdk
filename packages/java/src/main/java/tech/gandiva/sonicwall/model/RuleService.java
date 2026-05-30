package tech.gandiva.sonicwall.model;

public record RuleService(boolean matchAny, String name) {
  public static RuleService anyService() {
    return new RuleService(true, "");
  }
}
