package tech.gandiva.sonicwall.wire;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import tech.gandiva.sonicwall.internal.JsonMaps;
import tech.gandiva.sonicwall.model.IcmpSpec;
import tech.gandiva.sonicwall.model.PortRange;
import tech.gandiva.sonicwall.model.ServiceObject;
import tech.gandiva.sonicwall.model.ServiceProtocol;

public final class ServiceObjectWire {
  private ServiceObjectWire() {}

  public static Map<String, Object> toEnvelope(ServiceObject object) {
    Map<String, Object> proto = protocolWire(object.protocol());
    return Map.of(
        "service_object",
        Map.of("name", object.name(), "protocol", proto));
  }

  public static Map<String, Object> collectionPayload(ServiceObject object) {
    Map<String, Object> env = toEnvelope(object);
    return Map.of("service_objects", List.of(env.get("service_object")));
  }

  public static Map<String, Object> firmwareCollectionPayload(ServiceObject object) {
    Map<String, Object> row = new HashMap<>();
    row.put("name", object.name());
    ServiceProtocol protocol = object.protocol() != null ? object.protocol() : ServiceProtocol.empty();
    if (protocol.tcp() != null) {
      row.put("tcp", portWire(protocol.tcp()));
    }
    if (protocol.udp() != null) {
      row.put("udp", portWire(protocol.udp()));
    }
    if (protocol.icmp() != null) {
      row.put("icmp", icmpWire(protocol.icmp()));
    }
    return Map.of("service_objects", List.of(row));
  }

  public static ServiceObject fromApiItem(Map<String, Object> data) {
    Map<String, Object> inner = JsonMaps.asMap(data.get("service_object"));
    if (inner.isEmpty()) {
      inner = data;
    }

    ServiceProtocol protocol = parseProtocol(JsonMaps.asMap(inner.get("protocol")));
    if (protocol.tcp() == null) {
      PortRange tcp = parsePort(JsonMaps.asMap(inner.get("tcp")));
      if (tcp != null) {
        protocol = mergeProtocol(protocol, tcp, null, null);
      }
    }
    if (protocol.udp() == null) {
      PortRange udp = parsePort(JsonMaps.asMap(inner.get("udp")));
      if (udp != null) {
        protocol = mergeProtocol(protocol, null, udp, null);
      }
    }
    if (protocol.icmp() == null) {
      IcmpSpec icmp = parseIcmp(JsonMaps.asMap(inner.get("icmp")));
      if (icmp != null) {
        protocol = mergeProtocol(protocol, null, null, icmp);
      }
    }

    return new ServiceObject(JsonMaps.stringFromAny(inner.get("name")), protocol);
  }

  private static ServiceProtocol parseProtocol(Map<String, Object> rawProto) {
    PortRange tcp = parsePort(JsonMaps.asMap(rawProto.get("tcp")));
    PortRange udp = parsePort(JsonMaps.asMap(rawProto.get("udp")));
    IcmpSpec icmp = parseIcmp(JsonMaps.asMap(rawProto.get("icmp")));
    return new ServiceProtocol(tcp, udp, icmp);
  }

  private static ServiceProtocol mergeProtocol(
      ServiceProtocol base, PortRange tcp, PortRange udp, IcmpSpec icmp) {
    return new ServiceProtocol(
        tcp != null ? tcp : base.tcp(),
        udp != null ? udp : base.udp(),
        icmp != null ? icmp : base.icmp());
  }

  private static PortRange parsePort(Map<String, Object> map) {
    if (map.isEmpty()) {
      return null;
    }
    Integer begin = JsonMaps.intFromAny(map.get("begin"));
    Integer end = JsonMaps.intFromAny(map.get("end"));
    if (begin == null || end == null) {
      return null;
    }
    return new PortRange(begin, end);
  }

  private static IcmpSpec parseIcmp(Map<String, Object> map) {
    if (map.isEmpty()) {
      return null;
    }
    Integer type = JsonMaps.intFromAny(map.get("type"));
    if (type == null) {
      return null;
    }
    Integer code = JsonMaps.intFromAny(map.get("code"));
    return new IcmpSpec(type, code != null ? code : 0);
  }

  private static Map<String, Object> protocolWire(ServiceProtocol protocol) {
    Map<String, Object> proto = new HashMap<>();
    ServiceProtocol p = protocol != null ? protocol : ServiceProtocol.empty();
    if (p.tcp() != null) {
      proto.put("tcp", portWire(p.tcp()));
    }
    if (p.udp() != null) {
      proto.put("udp", portWire(p.udp()));
    }
    if (p.icmp() != null) {
      proto.put("icmp", icmpWire(p.icmp()));
    }
    return proto;
  }

  private static Map<String, Object> portWire(PortRange range) {
    return Map.of("begin", range.begin(), "end", range.end());
  }

  private static Map<String, Object> icmpWire(IcmpSpec icmp) {
    return Map.of("type", icmp.type(), "code", icmp.code());
  }
}
