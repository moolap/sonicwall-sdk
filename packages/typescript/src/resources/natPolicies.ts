/**
 * NatPoliciesResource — CRUD for SonicOS IPv4 NAT policies.
 */

import type { SonicWallClient } from "../client.ts";
import { NotFoundError, SonicWallHTTPError } from "../errors.ts";
import {
  natPolicyFirmwareCollectionPayload,
  natPolicyFromApiResponse,
  natPolicyToApiDict,
  type NatPolicy,
} from "../models/natPolicy.ts";
import { normalizeGetFromPlural, unwrapIpv4 } from "./normalize.ts";
import { BaseResource } from "./base.ts";

const BASE = "nat-policies/ipv4";

function toCollectionPayload(policy: NatPolicy): Record<string, unknown> {
  const single = natPolicyToApiDict(policy) as { nat_policy?: unknown };
  return { nat_policies: [single.nat_policy ?? single] };
}

function isSchemaArrayError(err: unknown): boolean {
  if (!(err instanceof SonicWallHTTPError) || err.statusCode !== 400) return false;
  const msg = err.message.toLowerCase();
  return (
    msg.includes("schema validation error") &&
    msg.includes("nat_policies") &&
    msg.includes("expected '['")
  );
}

export class NatPoliciesResource extends BaseResource {
  constructor(client: SonicWallClient) {
    super(client);
  }

  async list(): Promise<NatPolicy[]> {
    return this._list(
      BASE,
      "nat_policies",
      (item) => natPolicyFromApiResponse(item as Record<string, unknown>),
      true
    );
  }

  async get(name: string): Promise<NatPolicy> {
    const enc = encodeURIComponent(name);
    try {
      const response = await this._get<Record<string, unknown>>(`${BASE}/name/${enc}`);
      const normalized = normalizeGetFromPlural(response, {
        pluralKey: "nat_policies",
        singularKey: "nat_policy",
        predicate: (item) => {
          const ipv4 = unwrapIpv4(item, "nat_policy");
          return ipv4 != null && ipv4["name"] === name;
        },
      });
      return natPolicyFromApiResponse(normalized);
    } catch (err) {
      if (!(err instanceof NotFoundError)) {
        if (!(err instanceof SonicWallHTTPError) || err.statusCode !== 404) {
          throw err;
        }
      }
    }
    for (const p of await this.list()) {
      if (p.name === name) return p;
    }
    throw new NotFoundError(`NAT policy not found: ${name}`);
  }

  async create(policy: NatPolicy): Promise<NatPolicy> {
    const payload = natPolicyToApiDict(policy);
    try {
      await this._post(BASE, payload);
    } catch (err) {
      if (!isSchemaArrayError(err)) throw err;
      try {
        await this._post(BASE, toCollectionPayload(policy));
      } catch {
        await this._post(BASE, natPolicyFirmwareCollectionPayload(policy));
      }
    }
    if (policy.name) {
      try {
        return await this.get(policy.name);
      } catch {
        console.warn("Create succeeded but NAT get failed; returning input policy");
      }
    }
    return policy;
  }

  async update(name: string, policy: NatPolicy): Promise<NatPolicy> {
    const enc = encodeURIComponent(name);
    const path = `${BASE}/name/${enc}`;
    const payload = natPolicyToApiDict(policy);
    try {
      await this._put(path, payload);
    } catch (err) {
      if (!isSchemaArrayError(err)) throw err;
      try {
        await this._put(path, toCollectionPayload(policy));
      } catch {
        await this._put(path, natPolicyFirmwareCollectionPayload(policy));
      }
    }
    const effectiveName = policy.name ?? name;
    try {
      return await this.get(effectiveName);
    } catch {
      console.warn("Update succeeded but NAT get failed; returning input policy");
      return policy;
    }
  }

  async delete(name: string): Promise<void> {
    const enc = encodeURIComponent(name);
    await this._delete(`${BASE}/name/${enc}`);
  }

  async ensure(policy: NatPolicy): Promise<[NatPolicy, boolean]> {
    if (!policy.name) {
      const created = await this.create(policy);
      return [created, true];
    }
    try {
      await this.get(policy.name);
      const updated = await this.update(policy.name, policy);
      return [updated, false];
    } catch (err) {
      if (err instanceof NotFoundError) {
        const created = await this.create(policy);
        return [created, true];
      }
      throw err;
    }
  }
}
