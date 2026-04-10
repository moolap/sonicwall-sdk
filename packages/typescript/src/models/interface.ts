/**
 * SonicOS network interface (read-only).
 */

import { z } from "zod";

export const IPAssignmentSchema = z.enum(["static", "dhcp", "pppoe", "l2tp"]);

export const InterfaceSchema = z.object({
  name: z.string(),
  ipAssignment: IPAssignmentSchema.optional(),
  ip: z.string().optional(),
  subnet: z.string().optional(),
  zone: z.string().optional(),
  enabled: z.boolean().default(true),
  comment: z.string().optional(),
});

export type Interface = z.infer<typeof InterfaceSchema>;
export type IPAssignment = z.infer<typeof IPAssignmentSchema>;

export function interfaceFromApiResponse(data: Record<string, unknown>): Interface {
  let inner = data;
  if ("interface" in inner && typeof inner["interface"] === "object" && inner["interface"]) {
    inner = inner["interface"] as Record<string, unknown>;
  }
  return InterfaceSchema.parse({
    name: inner["name"] ?? "",
    ipAssignment: inner["ip_assignment"],
    ip: inner["ip"] != null ? String(inner["ip"]) : undefined,
    subnet: inner["subnet"] != null ? String(inner["subnet"]) : undefined,
    zone: inner["zone"] != null ? String(inner["zone"]) : undefined,
    enabled: inner["enabled"] !== false,
    comment: inner["comment"] != null ? String(inner["comment"]) : undefined,
  });
}
