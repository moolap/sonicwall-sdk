package tech.gandiva.sonicwall.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.internal.ApiTransport;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.NetworkInterface;
import tech.gandiva.sonicwall.wire.ResourceWire;

public final class InterfacesService {
  private static final String BASE = "/interfaces";

  private final ApiTransport transport;

  public InterfacesService(ApiTransport transport) {
    this.transport = transport;
  }

  public List<NetworkInterface> list() {
    Map<String, Object> top = ResourceHelpers.readTopMap(transport, transport.request("GET", BASE, null));
    List<NetworkInterface> out = new ArrayList<>();
    for (Map<String, Object> item : JsonMaps.listOfMaps(top.get("interfaces"))) {
      out.add(ResourceWire.interfaceFromApiItem(item));
    }
    return out;
  }

  public NetworkInterface get(String name) {
    Map<String, Object> top =
        ResourceHelpers.readTopMap(
            transport, transport.request("GET", BASE + "/name/" + ResourceHelpers.encode(name), null));
    return ResourceWire.interfaceFromApiItem(top);
  }
}
