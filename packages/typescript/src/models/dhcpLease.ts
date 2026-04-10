/**
 * DHCP server lease (read-only).
 */

import { z } from "zod";

export const DhcpLeaseSchema = z.object({
  ip: z.string(),
  mac: z.string(),
  hostname: z.string().optional(),
  expires: z.string().optional(),
  interface: z.string().optional(),
});

export type DhcpLease = z.infer<typeof DhcpLeaseSchema>;

export function dhcpLeaseFromApiResponse(data: Record<string, unknown>): DhcpLease {
  return DhcpLeaseSchema.parse({
    ip: data["ip"] != null ? String(data["ip"]) : "",
    mac: data["mac"] != null ? String(data["mac"]) : "",
    hostname: data["hostname"] != null ? String(data["hostname"]) : undefined,
    expires: data["expires"] != null ? String(data["expires"]) : undefined,
    interface: data["interface"] != null ? String(data["interface"]) : undefined,
  });
}
