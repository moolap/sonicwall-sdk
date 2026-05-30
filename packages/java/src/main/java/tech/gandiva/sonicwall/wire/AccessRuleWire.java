package tech.gandiva.sonicwall.wire;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.AccessRule;
import tech.gandiva.sonicwall.model.RuleAddress;
import tech.gandiva.sonicwall.model.RulePriority;
import tech.gandiva.sonicwall.model.RuleService;

public final class AccessRuleWire {
  private AccessRuleWire() {}

  public static Map<String, Object> toEnvelope(AccessRule rule) {
    Map<String, Object> inner = new HashMap<>();
    inner.put("from", rule.fromZone());
    inner.put("to", rule.toZone());
    inner.put("action", rule.action());
    inner.put("enabled", rule.enabled());
    inner.put("log", rule.log());
    inner.put("source", ruleAddrWire(rule.sourceAddress()));
    inner.put("destination", ruleAddrWire(rule.destinationAddress()));
    inner.put("service", ruleSvcWire(rule.service()));
    if (rule.name() != null && !rule.name().isBlank()) {
      inner.put("name", rule.name());
    }
    RulePriority priority = rule.priority() != null ? rule.priority() : RulePriority.automatic();
    if (priority.isAuto()) {
      inner.put("priority", Map.of("auto", true));
    } else if (priority.value() != null) {
      inner.put("priority", Map.of("value", priority.value()));
    }
    if (rule.comment() != null && !rule.comment().isBlank()) {
      inner.put("comment", rule.comment());
    }
    return Map.of("access_rule", Map.of("ipv4", inner));
  }

  public static Map<String, Object> collectionPayload(AccessRule rule) {
    Map<String, Object> env = toEnvelope(rule);
    return Map.of("access_rules", List.of(env.get("access_rule")));
  }

  public static AccessRule fromApiItem(Map<String, Object> data) {
    Map<String, Object> inner = JsonMaps.asMap(data.get("access_rule"));
    if (inner.isEmpty()) {
      inner = data;
    }
    Map<String, Object> ipv4 = JsonMaps.asMap(inner.get("ipv4"));
    if (!ipv4.isEmpty()) {
      inner = ipv4;
    }

    RulePriority priority = RulePriority.automatic();
    Map<String, Object> p = JsonMaps.asMap(inner.get("priority"));
    if (Boolean.TRUE.equals(p.get("auto"))) {
      priority = RulePriority.automatic();
    } else {
      Integer v = JsonMaps.intFromAny(p.get("value"));
      if (v != null) {
        priority = new RulePriority(false, v);
      }
    }

    RuleAddress source = RuleAddress.anyAddress();
    Map<String, Object> src = JsonMaps.asMap(inner.get("source"));
    Map<String, Object> srcAddr = JsonMaps.asMap(src.get("address"));
    if (!srcAddr.isEmpty()) {
      source = parseRuleAddr(srcAddr);
    }

    RuleAddress destination = RuleAddress.anyAddress();
    Map<String, Object> dst = JsonMaps.asMap(inner.get("destination"));
    Map<String, Object> dstAddr = JsonMaps.asMap(dst.get("address"));
    if (!dstAddr.isEmpty()) {
      destination = parseRuleAddr(dstAddr);
    }

    RuleService service = RuleService.anyService();
    Map<String, Object> svc = JsonMaps.asMap(inner.get("service"));
    if (!svc.isEmpty()) {
      service = parseRuleSvc(svc);
    }

    String action = JsonMaps.stringFromAny(inner.get("action"));
    if (action.isBlank()) {
      action = "allow";
    }

    return new AccessRule(
        JsonMaps.stringFromAny(inner.get("name")),
        JsonMaps.stringFromAny(inner.get("from")),
        JsonMaps.stringFromAny(inner.get("to")),
        action,
        JsonMaps.boolFromAny(inner.get("enabled"), true),
        Boolean.TRUE.equals(inner.get("log")),
        priority,
        source,
        destination,
        service,
        JsonMaps.stringFromAny(inner.get("comment")));
  }

  private static RuleAddress parseRuleAddr(Map<String, Object> addr) {
    if (Boolean.TRUE.equals(addr.get("any"))) {
      return RuleAddress.anyAddress();
    }
    String name = JsonMaps.stringFromAny(addr.get("name"));
    if (!name.isBlank()) {
      return new RuleAddress(false, name, "");
    }
    String group = JsonMaps.stringFromAny(addr.get("group"));
    if (!group.isBlank()) {
      return new RuleAddress(false, "", group);
    }
    return RuleAddress.anyAddress();
  }

  private static RuleService parseRuleSvc(Map<String, Object> svc) {
    if (Boolean.TRUE.equals(svc.get("any"))) {
      return RuleService.anyService();
    }
    String name = JsonMaps.stringFromAny(svc.get("name"));
    if (!name.isBlank()) {
      return new RuleService(false, name);
    }
    return RuleService.anyService();
  }

  private static Map<String, Object> ruleAddrWire(RuleAddress address) {
    RuleAddress a = address != null ? address : RuleAddress.anyAddress();
    if (a.matchAny()) {
      return Map.of("address", Map.of("any", true));
    }
    if (a.name() != null && !a.name().isBlank()) {
      return Map.of("address", Map.of("name", a.name()));
    }
    if (a.group() != null && !a.group().isBlank()) {
      return Map.of("address", Map.of("group", a.group()));
    }
    return Map.of("address", Map.of("any", true));
  }

  private static Map<String, Object> ruleSvcWire(RuleService service) {
    RuleService s = service != null ? service : RuleService.anyService();
    if (s.matchAny()) {
      return Map.of("any", true);
    }
    if (s.name() != null && !s.name().isBlank()) {
      return Map.of("name", s.name());
    }
    return Map.of("any", true);
  }
}
