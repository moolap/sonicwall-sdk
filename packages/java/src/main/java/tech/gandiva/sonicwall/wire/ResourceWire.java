package tech.gandiva.sonicwall.wire;

import java.util.Map;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.DhcpLease;
import tech.gandiva.sonicwall.model.NetworkInterface;

public final class ResourceWire {
  private ResourceWire() {}

  public static NetworkInterface interfaceFromApiItem(Map<String, Object> data) {
    Map<String, Object> inner = JsonMaps.asMap(data.get("interface"));
    if (inner.isEmpty()) {
      inner = data;
    }
    return new NetworkInterface(
        JsonMaps.stringFromAny(inner.get("name")),
        JsonMaps.stringFromAny(inner.get("ip_assignment")),
        JsonMaps.stringFromAny(inner.get("ip")),
        JsonMaps.stringFromAny(inner.get("subnet")),
        JsonMaps.stringFromAny(inner.get("zone")),
        JsonMaps.boolFromAny(inner.get("enabled"), true),
        JsonMaps.stringFromAny(inner.get("comment")));
  }

  public static DhcpLease dhcpLeaseFromMap(Map<String, Object> data) {
    return new DhcpLease(
        JsonMaps.stringFromAny(data.get("ip")),
        JsonMaps.stringFromAny(data.get("mac")),
        JsonMaps.stringFromAny(data.get("hostname")),
        JsonMaps.stringFromAny(data.get("expires")),
        JsonMaps.stringFromAny(data.get("interface")));
  }
}
