package tech.gandiva.sonicwall.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.exception.NotFoundException;
import tech.gandiva.sonicwall.internal.ApiNormalize;
import tech.gandiva.sonicwall.internal.ApiTransport;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.ServiceObject;
import tech.gandiva.sonicwall.wire.ServiceObjectWire;

public final class ServiceObjectsService {
  private static final String BASE = "/service-objects";

  private final ApiTransport transport;

  public ServiceObjectsService(ApiTransport transport) {
    this.transport = transport;
  }

  public List<ServiceObject> list() {
    Map<String, Object> top = ResourceHelpers.readTopMap(transport, transport.request("GET", BASE, null));
    List<ServiceObject> out = new ArrayList<>();
    for (Map<String, Object> item : JsonMaps.listOfMaps(top.get("service_objects"))) {
      out.add(ServiceObjectWire.fromApiItem(item));
    }
    return out;
  }

  public ServiceObject get(String name) {
    String path = BASE + "/name/" + ResourceHelpers.encode(name);
    try {
      Map<String, Object> top = ResourceHelpers.readTopMap(transport, transport.request("GET", path, null));
      Map<String, Object> norm =
          ApiNormalize.normalizeGetFromPlural(
              top,
              "service_objects",
              "service_object",
              item -> {
                Map<String, Object> so = JsonMaps.asMap(item.get("service_object"));
                if (!so.isEmpty() && name.equals(JsonMaps.stringFromAny(so.get("name")))) {
                  return true;
                }
                return name.equals(JsonMaps.stringFromAny(item.get("name")));
              });
      return ServiceObjectWire.fromApiItem(norm);
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isNotFound(ex)) {
        throw ex;
      }
      for (ServiceObject object : list()) {
        if (name.equals(object.name())) {
          return object;
        }
      }
      throw new NotFoundException("service object not found: " + name, 404, 0, null);
    }
  }

  public ServiceObject create(ServiceObject object) {
    postWithFallbacks(object);
    try {
      return get(object.name());
    } catch (NotFoundException ignored) {
      return object;
    }
  }

  public ServiceObject update(String name, ServiceObject object) {
    String path = BASE + "/name/" + ResourceHelpers.encode(name);
    putWithFallbacks(path, object);
    try {
      return get(object.name());
    } catch (NotFoundException ignored) {
      return object;
    }
  }

  public void delete(String name) {
    transport.request("DELETE", BASE + "/name/" + ResourceHelpers.encode(name), null);
  }

  public EnsureResult ensure(ServiceObject object) {
    try {
      get(object.name());
      ServiceObject updated = update(object.name(), object);
      return new EnsureResult(updated, false);
    } catch (NotFoundException ex) {
      ServiceObject created = create(object);
      return new EnsureResult(created, true);
    }
  }

  public record EnsureResult(ServiceObject object, boolean created) {}

  private void postWithFallbacks(ServiceObject object) {
    try {
      transport.request("POST", BASE, ServiceObjectWire.toEnvelope(object));
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isSchemaArrayError(ex, "service_objects")) {
        throw ex;
      }
      try {
        transport.request("POST", BASE, ServiceObjectWire.collectionPayload(object));
      } catch (RuntimeException ex2) {
        transport.request("POST", BASE, ServiceObjectWire.firmwareCollectionPayload(object));
      }
    }
  }

  private void putWithFallbacks(String path, ServiceObject object) {
    try {
      transport.request("PUT", path, ServiceObjectWire.toEnvelope(object));
    } catch (RuntimeException ex) {
      if (!ResourceHelpers.isSchemaArrayError(ex, "service_objects")) {
        throw ex;
      }
      try {
        transport.request("PUT", path, ServiceObjectWire.collectionPayload(object));
      } catch (RuntimeException ex2) {
        transport.request("PUT", path, ServiceObjectWire.firmwareCollectionPayload(object));
      }
    }
  }
}
