/**
 * AddressObject — Zod schema and type for SonicOS IPv4 address objects.
 */

import { z } from "zod";

export const AddressObjectTypeSchema = z.enum([
  "host",
  "range",
  "network",
  "fqdn",
  "mac",
]);

export type AddressObjectType = z.infer<typeof AddressObjectTypeSchema>;

// Inner schema — what we present to users
export const AddressObjectSchema = z.object({
  name: z.string().max(31),
  type: AddressObjectTypeSchema,
  zone: z.string().default("LAN"),
  // Type-specific fields
  host: z.string().ip({ version: "v4" }).optional(),
  network: z.string().optional(), // CIDR notation e.g. "10.0.0.0/24"
  rangeStart: z.string().ip({ version: "v4" }).optional(),
  rangeEnd: z.string().ip({ version: "v4" }).optional(),
  fqdn: z.string().optional(),
  mac: z.string().optional(),
});

export type AddressObject = z.infer<typeof AddressObjectSchema>;

// SonicOS API wire format
export interface AddressObjectIPv4Wire {
  name: string;
  zone: string;
  host?: { ip: string };
  network?: { subnet: string; mask: string };
  range?: { begin: string; end: string };
  fqdn?: { domain: string };
  mac?: { address: string };
}

export interface AddressObjectEnvelope {
  address_object: {
    ipv4: AddressObjectIPv4Wire;
  };
}

/**
 * Convert a subnet mask (dotted decimal) to prefix length.
 * e.g. "255.255.255.0" -> 24
 */
function maskToPrefixLength(mask: string): number {
  const parts = mask.split(".").map(Number);
  let bits = 0;
  for (const part of parts) {
    const bin = (part >>> 0).toString(2);
    bits += bin.split("").filter((b) => b === "1").length;
  }
  return bits;
}

/**
 * Convert a CIDR prefix length to dotted-decimal subnet mask.
 * e.g. 24 -> "255.255.255.0"
 */
function prefixLengthToMask(prefix: number): string {
  const mask = ~(0xffffffff >>> prefix);
  return [
    (mask >>> 24) & 0xff,
    (mask >>> 16) & 0xff,
    (mask >>> 8) & 0xff,
    mask & 0xff,
  ].join(".");
}

/** Serialize an AddressObject to the SonicOS API wire format. */
export function toApiDict(obj: AddressObject): AddressObjectEnvelope {
  const inner: AddressObjectIPv4Wire = {
    name: obj.name,
    zone: obj.zone,
  };

  switch (obj.type) {
    case "host":
      inner.host = { ip: obj.host! };
      break;
    case "network": {
      const [subnet, prefix] = (obj.network ?? "").split("/");
      inner.network = {
        subnet: subnet ?? "",
        mask: prefixLengthToMask(parseInt(prefix ?? "24", 10)),
      };
      break;
    }
    case "range":
      inner.range = { begin: obj.rangeStart!, end: obj.rangeEnd! };
      break;
    case "fqdn":
      inner.fqdn = { domain: obj.fqdn! };
      break;
    case "mac":
      inner.mac = { address: obj.mac! };
      break;
  }

  return { address_object: { ipv4: inner } };
}

/** Parse an AddressObject from a SonicOS API response. */
export function fromApiResponse(data: Record<string, unknown>): AddressObject {
  // Unwrap envelope layers
  let inner = data;
  if ("address_object" in inner) {
    inner = (inner.address_object as Record<string, unknown>);
  }
  if ("ipv4" in inner) {
    inner = (inner.ipv4 as Record<string, unknown>);
  }

  const wire = inner as AddressObjectIPv4Wire;
  const base = { name: wire.name, zone: wire.zone ?? "LAN" };

  if (wire.host) {
    return AddressObjectSchema.parse({ ...base, type: "host", host: wire.host.ip });
  }
  if (wire.network) {
    const prefixLen = maskToPrefixLength(wire.network.mask);
    return AddressObjectSchema.parse({
      ...base,
      type: "network",
      network: `${wire.network.subnet}/${prefixLen}`,
    });
  }
  if (wire.range) {
    return AddressObjectSchema.parse({
      ...base,
      type: "range",
      rangeStart: wire.range.begin,
      rangeEnd: wire.range.end,
    });
  }
  if (wire.fqdn) {
    return AddressObjectSchema.parse({ ...base, type: "fqdn", fqdn: wire.fqdn.domain });
  }
  if (wire.mac) {
    return AddressObjectSchema.parse({ ...base, type: "mac", mac: wire.mac.address });
  }

  throw new Error(`Cannot determine address object type from response: ${JSON.stringify(wire)}`);
}