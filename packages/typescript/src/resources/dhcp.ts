/**
 * DhcpResource — read access to SonicOS DHCP server leases.
 */

import type { SonicWallClient } from "../client.ts";
import { NotFoundError } from "../errors.ts";
import { dhcpLeaseFromApiResponse, type DhcpLease } from "../models/dhcpLease.ts";
import { BaseResource } from "./base.ts";

const CANDIDATE_PATHS = [
  "dhcp/server/lease",
  "dhcp/server/leases",
  "dhcp/leases",
  "dhcp-server/lease",
] as const;

const CANDIDATE_KEYS = ["dhcp_leases", "dhcp_server_leases", "leases"] as const;

export class DhcpResource extends BaseResource {
  constructor(client: SonicWallClient) {
    super(client);
  }

  /** Return all active DHCP server leases (tries firmware path variants). */
  async listLeases(): Promise<DhcpLease[]> {
    let lastNotFound: NotFoundError | undefined;
    for (const path of CANDIDATE_PATHS) {
      try {
        const body = await this._get<Record<string, unknown>>(path);
        let items: unknown[] | undefined;
        for (const key of CANDIDATE_KEYS) {
          const raw = body[key];
          if (Array.isArray(raw)) {
            items = raw;
            break;
          }
        }
        if (items === undefined) {
          const status = body["status"] as Record<string, unknown> | undefined;
          if (status?.["success"] === true) {
            return [];
          }
          console.warn(`Unexpected DHCP lease response shape on ${path}:`, body);
          return [];
        }
        const result: ReturnType<typeof dhcpLeaseFromApiResponse>[] = [];
        for (const item of items) {
          if (item && typeof item === "object") {
            try {
              result.push(
                dhcpLeaseFromApiResponse(item as Record<string, unknown>)
              );
            } catch {
              console.warn(`Skipping unparsable DHCP lease from ${path}:`, item);
            }
          }
        }
        return result;
      } catch (err) {
        if (err instanceof NotFoundError) {
          lastNotFound = err;
          continue;
        }
        throw err;
      }
    }
    if (lastNotFound) throw lastNotFound;
    return [];
  }
}
