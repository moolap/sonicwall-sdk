/**
 * SonicOS IPv4 NAT policy.
 */

import { z } from "zod";

export const NatPolicySchema = z.object({
  name: z.string().optional(),
  enabled: z.boolean().default(true),
  inboundInterface: z.string(),
  outboundInterface: z.string(),
  originalSource: z.string().default("any"),
  translatedSource: z.string().default("original"),
  originalDestination: z.string().default("any"),
  translatedDestination: z.string().default("original"),
  originalService: z.string().default("any"),
  translatedService: z.string().default("original"),
  comment: z.string().optional(),
});

export type NatPolicy = z.infer<typeof NatPolicySchema>;

function normRef(value: unknown, defaultVal: string): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    const o = value as Record<string, unknown>;
    if (o["any"]) return "any";
    if (o["original"]) return "original";
    if (typeof o["name"] === "string") return o["name"];
    if (typeof o["group"] === "string") return o["group"];
  }
  return defaultVal;
}

export function natPolicyToApiDict(policy: NatPolicy): Record<string, unknown> {
  const inner: Record<string, unknown> = {
    inbound_interface: policy.inboundInterface,
    outbound_interface: policy.outboundInterface,
    original_source: policy.originalSource,
    translated_source: policy.translatedSource,
    original_destination: policy.originalDestination,
    translated_destination: policy.translatedDestination,
    original_service: policy.originalService,
    translated_service: policy.translatedService,
    enabled: policy.enabled,
  };
  if (policy.name) inner["name"] = policy.name;
  if (policy.comment) inner["comment"] = policy.comment;
  return { nat_policy: { ipv4: inner } };
}

function refObj(value: string, allowOriginal: boolean): Record<string, unknown> {
  if (value === "any") return { any: true };
  if (allowOriginal && value === "original") return { original: true };
  return { name: value };
}

export function natPolicyFirmwareCollectionPayload(policy: NatPolicy): Record<string, unknown> {
  return {
    nat_policies: [
      {
        ipv4: {
          name: policy.name ?? "",
          inbound: policy.inboundInterface,
          outbound: policy.outboundInterface,
          source: refObj(policy.originalSource, false),
          translated_source: refObj(policy.translatedSource, true),
          destination: refObj(policy.originalDestination, false),
          translated_destination: refObj(policy.translatedDestination, true),
          service: refObj(policy.originalService, false),
          translated_service: refObj(policy.translatedService, true),
          enable: policy.enabled,
          comment: policy.comment ?? "",
        },
      },
    ],
  };
}

export function natPolicyFromApiResponse(data: Record<string, unknown>): NatPolicy {
  let inner = data;
  if ("nat_policy" in inner && typeof inner["nat_policy"] === "object" && inner["nat_policy"]) {
    inner = inner["nat_policy"] as Record<string, unknown>;
  }
  if ("ipv4" in inner && typeof inner["ipv4"] === "object" && inner["ipv4"]) {
    inner = inner["ipv4"] as Record<string, unknown>;
  }
  return NatPolicySchema.parse({
    name: inner["name"] != null ? String(inner["name"]) : undefined,
    enabled: inner["enable"] !== false && inner["enabled"] !== false,
    inboundInterface: String(inner["inbound_interface"] ?? inner["inbound"] ?? "any"),
    outboundInterface: String(inner["outbound_interface"] ?? inner["outbound"] ?? "any"),
    originalSource: normRef(inner["original_source"] ?? inner["source"], "any"),
    translatedSource: normRef(inner["translated_source"], "original"),
    originalDestination: normRef(inner["original_destination"] ?? inner["destination"], "any"),
    translatedDestination: normRef(inner["translated_destination"], "original"),
    originalService: normRef(inner["original_service"] ?? inner["service"], "any"),
    translatedService: normRef(inner["translated_service"], "original"),
    comment: inner["comment"] != null ? String(inner["comment"]) : undefined,
  });
}
