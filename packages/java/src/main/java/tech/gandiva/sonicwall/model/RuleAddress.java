package tech.gandiva.sonicwall.model;

public record RuleAddress(boolean matchAny, String name, String group) {
  public static RuleAddress anyAddress() {
    return new RuleAddress(true, "", "");
  }
}
