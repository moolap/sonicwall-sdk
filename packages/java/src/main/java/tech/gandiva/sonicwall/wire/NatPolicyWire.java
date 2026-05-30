package tech.gandiva.sonicwall.wire;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.NatPolicy;

public final class NatPolicyWire {
  private NatPolicyWire() {}

  public static Map<String, Object> toEnvelope(NatPolicy policy) {
    Map<String, Object> inner = new HashMap<>();
    inner.put("inbound_interface", policy.inboundInterface());
    inner.put("outbound_interface", policy.outboundInterface());
    inner.put("original_source", policy.originalSource());
    inner.put("translated_source", policy.translatedSource());
    inner.put("original_destination", policy.originalDestination());
    inner.put("translated_destination", policy.translatedDestination());
    inner.put("original_service", policy.originalService());
    inner.put("translated_service", policy.translatedService());
    inner.put("enabled", policy.enabled());
    if (policy.name() != null && !policy.name().isBlank()) {
      inner.put("name", policy.name());
    }
    if (policy.comment() != null && !policy.comment().isBlank()) {
      inner.put("comment", policy.comment());
    }
    return Map.of("nat_policy", Map.of("ipv4", inner));
  }

  public static Map<String, Object> collectionPayload(NatPolicy policy) {
    Map<String, Object> env = toEnvelope(policy);
    return Map.of("nat_policies", List.of(env.get("nat_policy")));
  }

  public static Map<String, Object> firmwareCollectionPayload(NatPolicy policy) {
    Map<String, Object> ipv4 = new HashMap<>();
    ipv4.put("name", policy.name());
    ipv4.put("inbound", policy.inboundInterface());
    ipv4.put("outbound", policy.outboundInterface());
    ipv4.put("source", refObj(policy.originalSource(), false));
    ipv4.put("translated_source", refObj(policy.translatedSource(), true));
    ipv4.put("destination", refObj(policy.originalDestination(), false));
    ipv4.put("translated_destination", refObj(policy.translatedDestination(), true));
    ipv4.put("service", refObj(policy.originalService(), false));
    ipv4.put("translated_service", refObj(policy.translatedService(), true));
    ipv4.put("enable", policy.enabled());
    ipv4.put("comment", policy.comment());
    return Map.of("nat_policies", List.of(Map.of("ipv4", ipv4)));
  }

  public static NatPolicy fromApiItem(Map<String, Object> data) {
    Map<String, Object> inner = JsonMaps.asMap(data.get("nat_policy"));
    if (inner.isEmpty()) {
      inner = data;
    }
    Map<String, Object> ipv4 = JsonMaps.asMap(inner.get("ipv4"));
    if (!ipv4.isEmpty()) {
      inner = ipv4;
    }

    boolean enabled = JsonMaps.boolFromAny(inner.get("enabled"), true);
    if (Boolean.FALSE.equals(inner.get("enable"))) {
      enabled = false;
    }

    String inbound = JsonMaps.stringFromAny(inner.get("inbound_interface"));
    if (inbound.isBlank()) {
      inbound = JsonMaps.stringFromAny(inner.get("inbound"));
    }
    String outbound = JsonMaps.stringFromAny(inner.get("outbound_interface"));
    if (outbound.isBlank()) {
      outbound = JsonMaps.stringFromAny(inner.get("outbound"));
    }

    String originalSource = normRef(inner.get("original_source"), "any");
    if (originalSource.isBlank() || "any".equals(originalSource)) {
      originalSource = normRef(inner.get("source"), "any");
    }
    String originalDestination = normRef(inner.get("original_destination"), "any");
    if (originalDestination.isBlank() || "any".equals(originalDestination)) {
      originalDestination = normRef(inner.get("destination"), "any");
    }
    String originalService = normRef(inner.get("original_service"), "any");
    if (originalService.isBlank() || "any".equals(originalService)) {
      originalService = normRef(inner.get("service"), "any");
    }

    return new NatPolicy(
        JsonMaps.stringFromAny(inner.get("name")),
        enabled,
        inbound,
        outbound,
        originalSource,
        normRef(inner.get("translated_source"), "original"),
        originalDestination,
        normRef(inner.get("translated_destination"), "original"),
        originalService,
        normRef(inner.get("translated_service"), "original"),
        JsonMaps.stringFromAny(inner.get("comment")));
  }

  private static String normRef(Object value, String defaultVal) {
    if (value instanceof String s) {
      return s;
    }
    Map<String, Object> map = JsonMaps.asMap(value);
    if (map.isEmpty()) {
      return defaultVal;
    }
    if (Boolean.TRUE.equals(map.get("any"))) {
      return "any";
    }
    if (Boolean.TRUE.equals(map.get("original"))) {
      return "original";
    }
    String name = JsonMaps.stringFromAny(map.get("name"));
    if (!name.isBlank()) {
      return name;
    }
    String group = JsonMaps.stringFromAny(map.get("group"));
    if (!group.isBlank()) {
      return group;
    }
    return defaultVal;
  }

  private static Map<String, Object> refObj(String value, boolean allowOriginal) {
    if ("any".equals(value)) {
      return Map.of("any", true);
    }
    if (allowOriginal && "original".equals(value)) {
      return Map.of("original", true);
    }
    return Map.of("name", value);
  }
}
