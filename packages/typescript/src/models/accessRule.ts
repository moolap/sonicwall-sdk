/**
 * SonicOS IPv4 access rule.
 */

import { z } from "zod";

export const AccessRuleActionSchema = z.enum(["allow", "deny", "discard"]);
export type AccessRuleAction = z.infer<typeof AccessRuleActionSchema>;

export const RuleAddressSchema = z.object({
  any: z.boolean().default(false),
  name: z.string().optional(),
  group: z.string().optional(),
});

export const RuleServiceSchema = z.object({
  any: z.boolean().default(false),
  name: z.string().optional(),
});

export const RulePrioritySchema = z.object({
  auto: z.boolean().default(true),
  value: z.number().int().optional(),
});

export const AccessRuleSchema = z.object({
  name: z.string().max(31).optional(),
  fromZone: z.string(),
  toZone: z.string(),
  action: AccessRuleActionSchema.default("allow"),
  enabled: z.boolean().default(true),
  log: z.boolean().default(false),
  priority: RulePrioritySchema.default({ auto: true }),
  sourceAddress: RuleAddressSchema.default({ any: true }),
  destinationAddress: RuleAddressSchema.default({ any: true }),
  service: RuleServiceSchema.default({ any: true }),
  comment: z.string().max(255).optional(),
});

export type RuleAddress = z.infer<typeof RuleAddressSchema>;
export type RuleService = z.infer<typeof RuleServiceSchema>;
export type RulePriority = z.infer<typeof RulePrioritySchema>;
export type AccessRule = z.infer<typeof AccessRuleSchema>;

function addrWire(addr: RuleAddress): Record<string, unknown> {
  if (addr.any) return { address: { any: true } };
  if (addr.name) return { address: { name: addr.name } };
  if (addr.group) return { address: { group: addr.group } };
  return { address: { any: true } };
}

function svcWire(svc: RuleService): Record<string, unknown> {
  if (svc.any) return { any: true };
  if (svc.name) return { name: svc.name };
  return { any: true };
}

export function accessRuleToApiDict(rule: AccessRule): Record<string, unknown> {
  const inner: Record<string, unknown> = {
    from: rule.fromZone,
    to: rule.toZone,
    action: rule.action,
    enabled: rule.enabled,
    log: rule.log,
    source: addrWire(rule.sourceAddress),
    destination: addrWire(rule.destinationAddress),
    service: svcWire(rule.service),
  };
  if (rule.name) inner["name"] = rule.name;
  if (rule.priority.auto) {
    inner["priority"] = { auto: true };
  } else if (rule.priority.value != null) {
    inner["priority"] = { value: rule.priority.value };
  }
  if (rule.comment) inner["comment"] = rule.comment;
  return { access_rule: { ipv4: inner } };
}

export function accessRuleFromApiResponse(data: Record<string, unknown>): AccessRule {
  let inner = data;
  if ("access_rule" in inner && typeof inner["access_rule"] === "object" && inner["access_rule"]) {
    inner = inner["access_rule"] as Record<string, unknown>;
  }
  if ("ipv4" in inner && typeof inner["ipv4"] === "object" && inner["ipv4"]) {
    inner = inner["ipv4"] as Record<string, unknown>;
  }

  const prioRaw = inner["priority"] as Record<string, unknown> | undefined;
  let priority: RulePriority = { auto: true };
  if (prioRaw && typeof prioRaw === "object") {
    if (prioRaw["auto"] === true) priority = { auto: true };
    else if (typeof prioRaw["value"] === "number") priority = { auto: false, value: prioRaw["value"] };
  }

  const src = (inner["source"] as Record<string, unknown>)?.["address"] as Record<string, unknown> | undefined;
  let sourceAddress: RuleAddress = { any: true };
  if (src?.["any"]) sourceAddress = { any: true };
  else if (typeof src?.["name"] === "string") sourceAddress = { any: false, name: src["name"] };
  else if (typeof src?.["group"] === "string") sourceAddress = { any: false, group: src["group"] };

  const dst = (inner["destination"] as Record<string, unknown>)?.["address"] as
    | Record<string, unknown>
    | undefined;
  let destinationAddress: RuleAddress = { any: true };
  if (dst?.["any"]) destinationAddress = { any: true };
  else if (typeof dst?.["name"] === "string") destinationAddress = { any: false, name: dst["name"] };
  else if (typeof dst?.["group"] === "string") destinationAddress = { any: false, group: dst["group"] };

  const svc = inner["service"] as Record<string, unknown> | undefined;
  let service: RuleService = { any: true };
  if (svc && typeof svc === "object") {
    if (svc["any"]) service = { any: true };
    else if (typeof svc["name"] === "string") service = { any: false, name: svc["name"] };
  }

  return AccessRuleSchema.parse({
    name: inner["name"] != null ? String(inner["name"]) : undefined,
    fromZone: String(inner["from"] ?? ""),
    toZone: String(inner["to"] ?? ""),
    action: (inner["action"] as AccessRuleAction) ?? "allow",
    enabled: inner["enabled"] !== false,
    log: inner["log"] === true,
    priority,
    sourceAddress,
    destinationAddress,
    service,
    comment: inner["comment"] != null ? String(inner["comment"]) : undefined,
  });
}
