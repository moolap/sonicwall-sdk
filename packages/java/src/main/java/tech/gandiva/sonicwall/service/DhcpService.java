package tech.gandiva.sonicwall.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.internal.ApiTransport;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.DhcpLease;
import tech.gandiva.sonicwall.wire.ResourceWire;

public final class DhcpService {
  private static final String[] CANDIDATE_PATHS = {
    "/dhcp/server/lease",
    "/dhcp/server/leases",
    "/dhcp/leases",
    "/dhcp-server/lease"
  };

  private static final String[] CANDIDATE_KEYS = {
    "dhcp_leases", "dhcp_server_leases", "leases"
  };

  private final ApiTransport transport;

  public DhcpService(ApiTransport transport) {
    this.transport = transport;
  }

  public List<DhcpLease> listLeases() {
    RuntimeException lastNotFound = null;
    for (String path : CANDIDATE_PATHS) {
      try {
        Map<String, Object> top = ResourceHelpers.readTopMap(transport, transport.request("GET", path, null));
        List<Map<String, Object>> items = null;
        for (String key : CANDIDATE_KEYS) {
          List<Map<String, Object>> candidate = JsonMaps.listOfMaps(top.get(key));
          if (!candidate.isEmpty()) {
            items = candidate;
            break;
          }
        }
        if (items == null) {
          Map<String, Object> status = JsonMaps.asMap(top.get("status"));
          if (Boolean.TRUE.equals(status.get("success"))) {
            return List.of();
          }
          return List.of();
        }
        List<DhcpLease> out = new ArrayList<>();
        for (Map<String, Object> item : items) {
          out.add(ResourceWire.dhcpLeaseFromMap(item));
        }
        return out;
      } catch (RuntimeException ex) {
        if (ResourceHelpers.isNotFound(ex)) {
          lastNotFound = ex;
          continue;
        }
        throw ex;
      }
    }
    if (lastNotFound != null) {
      throw lastNotFound;
    }
    return List.of();
  }
}
