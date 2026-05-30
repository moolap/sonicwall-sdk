package tech.gandiva.sonicwall.service;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.exception.NotFoundException;
import tech.gandiva.sonicwall.internal.ApiTransport;
import tech.gandiva.sonicwall.model.AddressObject;
import tech.gandiva.sonicwall.wire.AddressObjectWire;

public final class AddressObjectsService {
  private static final String BASE = "/address-objects/ipv4";

  private final ApiTransport transport;

  public AddressObjectsService(ApiTransport transport) {
    this.transport = transport;
  }

  public List<AddressObject> list() {
    AddressObjectWire.ListResponse resp = transport.readValue(transport.request("GET", BASE, null), AddressObjectWire.ListResponse.class);
    List<AddressObject> out = new ArrayList<>();
    if (resp.addressObjects == null) {
      return out;
    }
    for (AddressObjectWire.Envelope item : resp.addressObjects) {
      if (item.addressObject != null && item.addressObject.ipv4 != null) {
        out.add(AddressObjectWire.fromWire(item.addressObject.ipv4));
      }
    }
    return out;
  }

  public AddressObject get(String name) {
    String path = BASE + "/name/" + encode(name);
    byte[] data = transport.request("GET", path, null);
    AddressObjectWire.Envelope env = transport.readValue(data, AddressObjectWire.Envelope.class);
    if (env.addressObject != null && env.addressObject.ipv4 != null && env.addressObject.ipv4.name != null) {
      return AddressObjectWire.fromWire(env.addressObject.ipv4);
    }
    AddressObjectWire.ListResponse list = transport.readValue(data, AddressObjectWire.ListResponse.class);
    if (list.addressObjects != null) {
      for (AddressObjectWire.Envelope item : list.addressObjects) {
        if (item.addressObject != null
            && item.addressObject.ipv4 != null
            && name.equals(item.addressObject.ipv4.name)) {
          return AddressObjectWire.fromWire(item.addressObject.ipv4);
        }
      }
      if (!list.addressObjects.isEmpty()
          && list.addressObjects.get(0).addressObject != null
          && list.addressObjects.get(0).addressObject.ipv4 != null) {
        return AddressObjectWire.fromWire(list.addressObjects.get(0).addressObject.ipv4);
      }
    }
    throw new NotFoundException("object not found", 404, 0, null);
  }

  public AddressObject create(AddressObject obj) {
    try {
      postWithFallback(BASE, AddressObjectWire.toEnvelope(obj));
    } catch (RuntimeException ex) {
      if (isSchemaArrayError(ex)) {
        postWithFallback(BASE, arrayFallback(obj));
      } else {
        throw ex;
      }
    }
    try {
      return get(obj.name());
    } catch (NotFoundException ex) {
      return obj;
    }
  }

  public AddressObject update(String name, AddressObject obj) {
    String path = BASE + "/name/" + encode(name);
    try {
      transport.request("PUT", path, AddressObjectWire.toEnvelope(obj));
    } catch (RuntimeException ex) {
      if (isSchemaArrayError(ex)) {
        transport.request("PUT", path, arrayFallback(obj));
      } else {
        throw ex;
      }
    }
    String effectiveName = obj.name() != null && !obj.name().isBlank() ? obj.name() : name;
    try {
      return get(effectiveName);
    } catch (NotFoundException ex) {
      return obj;
    }
  }

  public void delete(String name) {
    transport.request("DELETE", BASE + "/name/" + encode(name), null);
  }

  public EnsureResult ensure(AddressObject obj) {
    try {
      get(obj.name());
      AddressObject updated = update(obj.name(), obj);
      return new EnsureResult(updated, false);
    } catch (NotFoundException ex) {
      AddressObject created = create(obj);
      return new EnsureResult(created, true);
    }
  }

  public record EnsureResult(AddressObject object, boolean created) {}

  private void postWithFallback(String path, Object body) {
    transport.request("POST", path, body);
  }

  private static Map<String, Object> arrayFallback(AddressObject obj) {
    AddressObjectWire.Envelope env = AddressObjectWire.toEnvelope(obj);
    Map<String, Object> ipv4 = new HashMap<>();
    ipv4.put("name", env.addressObject.ipv4.name);
    ipv4.put("zone", env.addressObject.ipv4.zone);
    if (env.addressObject.ipv4.host != null) {
      ipv4.put("host", env.addressObject.ipv4.host);
    }
    if (env.addressObject.ipv4.network != null) {
      ipv4.put("network", env.addressObject.ipv4.network);
    }
    if (env.addressObject.ipv4.range != null) {
      ipv4.put("range", env.addressObject.ipv4.range);
    }
    if (env.addressObject.ipv4.fqdn != null) {
      ipv4.put("fqdn", env.addressObject.ipv4.fqdn);
    }
    if (env.addressObject.ipv4.mac != null) {
      ipv4.put("mac", env.addressObject.ipv4.mac);
    }
    Map<String, Object> item = Map.of("ipv4", ipv4);
    return Map.of("address_objects", List.of(item));
  }

  private static boolean isSchemaArrayError(RuntimeException ex) {
    String msg = ex.getMessage() == null ? "" : ex.getMessage().toLowerCase();
    return msg.contains("schema validation error") && msg.contains("address_objects");
  }

  private static String encode(String value) {
    return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
  }
}
