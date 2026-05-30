package tech.gandiva.sonicwall.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.exception.NotFoundException;
import tech.gandiva.sonicwall.internal.ApiNormalize;
import tech.gandiva.sonicwall.internal.ApiTransport;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.AccessRule;
import tech.gandiva.sonicwall.model.RulePriority;
import tech.gandiva.sonicwall.wire.AccessRuleWire;

public final class AccessRulesService {
  private static final String BASE = "/access-rules/ipv4";

  private final ApiTransport transport;

  public AccessRulesService(ApiTransport transport) {
    this.transport = transport;
  }

  public List<AccessRule> list() {
    Map<String, Object> top = ResourceHelpers.readTopMap(transport, transport.request("GET", BASE, null));
    List<AccessRule> out = new ArrayList<>();
    for (Map<String, Object> item : JsonMaps.listOfMaps(top.get("access_rules"))) {
      out.add(AccessRuleWire.fromApiItem(item));
    }
    return out;
  }

  public AccessRule get(String fromZone, String toZone, String name) {
    String path =
        BASE
            + "/from/"
            + ResourceHelpers.encode(fromZone)
            + "/to/"
            + ResourceHelpers.encode(toZone)
            + "/name/"
            + ResourceHelpers.encode(name);
    try {
      Map<String, Object> top = ResourceHelpers.readTopMap(transport, transport.request("GET", path, null));
      Map<String, Object> norm =
          ApiNormalize.normalizeGetFromPlural(
              top,
              "access_rules",
              "access_rule",
              item -> {
                Map<String, Object> ipv4 = ApiNormalize.unwrapIPv4(item, "access_rule");
                return ipv4 != null
                    && fromZone.equals(JsonMaps.stringFromAny(ipv4.get("from")))
                    && toZone.equals(JsonMaps.stringFromAny(ipv4.get("to")))
                    && name.equals(JsonMaps.stringFromAny(ipv4.get("name")));
              });
      return AccessRuleWire.fromApiItem(norm);
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isNotFound(ex)) {
        throw ex;
      }
      for (AccessRule rule : list()) {
        if (fromZone.equals(rule.fromZone()) && toZone.equals(rule.toZone()) && name.equals(rule.name())) {
          return rule;
        }
      }
      throw new NotFoundException(
          "access rule not found: " + fromZone + "->" + toZone + ":" + name, 404, 0, null);
    }
  }

  public AccessRule create(AccessRule rule) {
    try {
      transport.request("POST", BASE, AccessRuleWire.toEnvelope(rule));
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isSchemaArrayError(ex, "access_rules")) {
        throw ex;
      }
      transport.request("POST", BASE, AccessRuleWire.collectionPayload(rule));
    }
    if (rule.name() != null && !rule.name().isBlank()) {
      try {
        return get(rule.fromZone(), rule.toZone(), rule.name());
      } catch (NotFoundException ignored) {
        // fall through
      }
    }
    return rule;
  }

  public AccessRule update(String fromZone, String toZone, String name, AccessRule rule) {
    String path =
        BASE
            + "/from/"
            + ResourceHelpers.encode(fromZone)
            + "/to/"
            + ResourceHelpers.encode(toZone)
            + "/name/"
            + ResourceHelpers.encode(name);
    try {
      transport.request("PUT", path, AccessRuleWire.toEnvelope(rule));
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isSchemaArrayError(ex, "access_rules")) {
        throw ex;
      }
      transport.request("PUT", path, AccessRuleWire.collectionPayload(rule));
    }
    String effective = rule.name() != null && !rule.name().isBlank() ? rule.name() : name;
    try {
      return get(rule.fromZone(), rule.toZone(), effective);
    } catch (NotFoundException ignored) {
      return rule;
    }
  }

  public void delete(String fromZone, String toZone, String name) {
    String path =
        BASE
            + "/from/"
            + ResourceHelpers.encode(fromZone)
            + "/to/"
            + ResourceHelpers.encode(toZone)
            + "/name/"
            + ResourceHelpers.encode(name);
    transport.request("DELETE", path, null);
  }

  public AccessRule insertBefore(AccessRule rule, String beforeName) {
    AccessRule adjusted = rule;
    try {
      AccessRule target = get(rule.fromZone(), rule.toZone(), beforeName);
      RulePriority priority = target.priority();
      if (priority != null && !priority.isAuto() && priority.value() != null) {
        adjusted =
            new AccessRule(
                rule.name(),
                rule.fromZone(),
                rule.toZone(),
                rule.action(),
                rule.enabled(),
                rule.log(),
                new RulePriority(false, priority.value()),
                rule.sourceAddress(),
                rule.destinationAddress(),
                rule.service(),
                rule.comment());
      }
    } catch (NotFoundException ignored) {
      // keep original priority
    }
    return create(adjusted);
  }

  public AccessRule insertAfter(AccessRule rule, String afterName) {
    AccessRule adjusted = rule;
    try {
      AccessRule target = get(rule.fromZone(), rule.toZone(), afterName);
      RulePriority priority = target.priority();
      if (priority != null && !priority.isAuto() && priority.value() != null) {
        adjusted =
            new AccessRule(
                rule.name(),
                rule.fromZone(),
                rule.toZone(),
                rule.action(),
                rule.enabled(),
                rule.log(),
                new RulePriority(false, priority.value() + 1),
                rule.sourceAddress(),
                rule.destinationAddress(),
                rule.service(),
                rule.comment());
      }
    } catch (NotFoundException ignored) {
      // keep original priority
    }
    return create(adjusted);
  }
}
