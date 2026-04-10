/**
 * SonicOS service object.
 */

import { z } from "zod";

export const PortRangeSchema = z.object({
  begin: z.number().int().min(0).max(65535),
  end: z.number().int().min(0).max(65535),
});

export const IcmpSpecSchema = z.object({
  type: z.number().int().min(0).max(255),
  code: z.number().int().min(0).max(255).default(0),
});

export const ServiceProtocolSchema = z.object({
  tcp: PortRangeSchema.optional(),
  udp: PortRangeSchema.optional(),
  icmp: IcmpSpecSchema.optional(),
});

export const ServiceObjectSchema = z.object({
  name: z.string(),
  protocol: ServiceProtocolSchema,
});

export type PortRange = z.infer<typeof PortRangeSchema>;
export type IcmpSpec = z.infer<typeof IcmpSpecSchema>;
export type ServiceProtocol = z.infer<typeof ServiceProtocolSchema>;
export type ServiceObject = z.infer<typeof ServiceObjectSchema>;

export function serviceObjectToApiDict(obj: ServiceObject): Record<string, unknown> {
  const proto: Record<string, unknown> = {};
  if (obj.protocol.tcp) {
    proto["tcp"] = { begin: obj.protocol.tcp.begin, end: obj.protocol.tcp.end };
  }
  if (obj.protocol.udp) {
    proto["udp"] = { begin: obj.protocol.udp.begin, end: obj.protocol.udp.end };
  }
  if (obj.protocol.icmp) {
    proto["icmp"] = { type: obj.protocol.icmp.type, code: obj.protocol.icmp.code };
  }
  return {
    service_object: {
      name: obj.name,
      protocol: proto,
    },
  };
}

export function firmwareServiceObjectCollectionPayload(obj: ServiceObject): Record<string, unknown> {
  const row: Record<string, unknown> = { name: obj.name };
  if (obj.protocol.tcp) {
    row["tcp"] = { begin: obj.protocol.tcp.begin, end: obj.protocol.tcp.end };
  }
  if (obj.protocol.udp) {
    row["udp"] = { begin: obj.protocol.udp.begin, end: obj.protocol.udp.end };
  }
  if (obj.protocol.icmp) {
    row["icmp"] = { type: obj.protocol.icmp.type, code: obj.protocol.icmp.code };
  }
  return { service_objects: [row] };
}

export function serviceObjectFromApiResponse(data: Record<string, unknown>): ServiceObject {
  let inner = data;
  if ("service_object" in inner && typeof inner["service_object"] === "object" && inner["service_object"]) {
    inner = inner["service_object"] as Record<string, unknown>;
  }
  const rawProto = (inner["protocol"] as Record<string, unknown>) ?? {};
  const proto: ServiceProtocol = {};
  const tcp = rawProto["tcp"] as Record<string, unknown> | undefined;
  if (tcp && typeof tcp["begin"] === "number" && typeof tcp["end"] === "number") {
    proto.tcp = { begin: tcp["begin"], end: tcp["end"] };
  }
  const udp = rawProto["udp"] as Record<string, unknown> | undefined;
  if (udp && typeof udp["begin"] === "number" && typeof udp["end"] === "number") {
    proto.udp = { begin: udp["begin"], end: udp["end"] };
  }
  const icmp = rawProto["icmp"] as Record<string, unknown> | undefined;
  if (icmp && typeof icmp["type"] === "number") {
    proto.icmp = { type: icmp["type"], code: typeof icmp["code"] === "number" ? icmp["code"] : 0 };
  }
  return ServiceObjectSchema.parse({
    name: String(inner["name"] ?? ""),
    protocol: proto,
  });
}
