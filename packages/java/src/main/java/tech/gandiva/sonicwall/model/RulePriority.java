package tech.gandiva.sonicwall.model;

public record RulePriority(boolean isAuto, Integer value) {
  public static RulePriority automatic() {
    return new RulePriority(true, null);
  }
}
