package tech.gandiva.sonicwall.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.exception.NotFoundException;
import tech.gandiva.sonicwall.internal.ApiNormalize;
import tech.gandiva.sonicwall.internal.ApiTransport;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.NatPolicy;
import tech.gandiva.sonicwall.wire.NatPolicyWire;

public final class NatPoliciesService {
  private static final String BASE = "/nat-policies/ipv4";

  private final ApiTransport transport;

  public NatPoliciesService(ApiTransport transport) {
    this.transport = transport;
  }

  public List<NatPolicy> list() {
    Map<String, Object> top = ResourceHelpers.readTopMap(transport, transport.request("GET", BASE, null));
    List<NatPolicy> out = new ArrayList<>();
    for (Map<String, Object> item : JsonMaps.listOfMaps(top.get("nat_policies"))) {
      out.add(NatPolicyWire.fromApiItem(item));
    }
    return out;
  }

  public NatPolicy get(String name) {
    String path = BASE + "/name/" + ResourceHelpers.encode(name);
    try {
      Map<String, Object> top = ResourceHelpers.readTopMap(transport, transport.request("GET", path, null));
      Map<String, Object> norm =
          ApiNormalize.normalizeGetFromPlural(
              top,
              "nat_policies",
              "nat_policy",
              item -> {
                Map<String, Object> ipv4 = ApiNormalize.unwrapIPv4(item, "nat_policy");
                return ipv4 != null && name.equals(JsonMaps.stringFromAny(ipv4.get("name")));
              });
      return NatPolicyWire.fromApiItem(norm);
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isNotFound(ex)) {
        throw ex;
      }
      for (NatPolicy policy : list()) {
        if (name.equals(policy.name())) {
          return policy;
        }
      }
      throw new NotFoundException("NAT policy not found: " + name, 404, 0, null);
    }
  }

  public NatPolicy create(NatPolicy policy) {
    postWithFallbacks(policy);
    if (policy.name() != null && !policy.name().isBlank()) {
      try {
        return get(policy.name());
      } catch (NotFoundException ignored) {
        // fall through
      }
    }
    return policy;
  }

  public NatPolicy update(String name, NatPolicy policy) {
    String path = BASE + "/name/" + ResourceHelpers.encode(name);
    putWithFallbacks(path, policy);
    String effective = policy.name() != null && !policy.name().isBlank() ? policy.name() : name;
    try {
      return get(effective);
    } catch (NotFoundException ignored) {
      return policy;
    }
  }

  public void delete(String name) {
    transport.request("DELETE", BASE + "/name/" + ResourceHelpers.encode(name), null);
  }

  public EnsureResult ensure(NatPolicy policy) {
    if (policy.name() == null || policy.name().isBlank()) {
      NatPolicy created = create(policy);
      return new EnsureResult(created, true);
    }
    try {
      get(policy.name());
      NatPolicy updated = update(policy.name(), policy);
      return new EnsureResult(updated, false);
    } catch (NotFoundException ex) {
      NatPolicy created = create(policy);
      return new EnsureResult(created, true);
    }
  }

  public record EnsureResult(NatPolicy policy, boolean created) {}

  private void postWithFallbacks(NatPolicy policy) {
    try {
      transport.request("POST", BASE, NatPolicyWire.toEnvelope(policy));
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isSchemaArrayError(ex, "nat_policies")) {
        throw ex;
      }
      try {
        transport.request("POST", BASE, NatPolicyWire.collectionPayload(policy));
      } catch (RuntimeException ex2) {
        transport.request("POST", BASE, NatPolicyWire.firmwareCollectionPayload(policy));
      }
    }
  }

  private void putWithFallbacks(String path, NatPolicy policy) {
    try {
      transport.request("PUT", path, NatPolicyWire.toEnvelope(policy));
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isSchemaArrayError(ex, "nat_policies")) {
        throw ex;
      }
      try {
        transport.request("PUT", path, NatPolicyWire.collectionPayload(policy));
      } catch (RuntimeException ex2) {
        transport.request("PUT", path, NatPolicyWire.firmwareCollectionPayload(policy));
      }
    }
  }
}
