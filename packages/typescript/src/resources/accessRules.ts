/**
 * AccessRulesResource — CRUD for SonicOS IPv4 access rules.
 */

import type { SonicWallClient } from "../client.ts";
import {
  accessRuleFromApiResponse,
  accessRuleToApiDict,
  type AccessRule,
} from "../models/accessRule.ts";
import { NotFoundError, SonicWallHTTPError } from "../errors.ts";
import { normalizeGetFromPlural, unwrapIpv4 } from "./normalize.ts";
import { BaseResource } from "./base.ts";

const BASE = "access-rules/ipv4";

function toCollectionPayload(rule: AccessRule): Record<string, unknown> {
  const single = accessRuleToApiDict(rule) as { access_rule?: unknown };
  return { access_rules: [single.access_rule ?? single] };
}

function isSchemaArrayError(err: unknown): boolean {
  if (!(err instanceof SonicWallHTTPError) || err.statusCode !== 400) return false;
  const msg = err.message.toLowerCase();
  return (
    msg.includes("schema validation error") &&
    msg.includes("access_rules") &&
    msg.includes("expected '['")
  );
}

export class AccessRulesResource extends BaseResource {
  constructor(client: SonicWallClient) {
    super(client);
  }

  async list(): Promise<AccessRule[]> {
    return this._list(
      BASE,
      "access_rules",
      (item) => accessRuleFromApiResponse(item as Record<string, unknown>),
      true
    );
  }

  async get(fromZone: string, toZone: string, name: string): Promise<AccessRule> {
    const fromEnc = encodeURIComponent(fromZone);
    const toEnc = encodeURIComponent(toZone);
    const nameEnc = encodeURIComponent(name);
    const path = `${BASE}/from/${fromEnc}/to/${toEnc}/name/${nameEnc}`;
    try {
      const response = await this._get<Record<string, unknown>>(path);
      const normalized = normalizeGetFromPlural(response, {
        pluralKey: "access_rules",
        singularKey: "access_rule",
        predicate: (item) => {
          const ipv4 = unwrapIpv4(item, "access_rule");
          return (
            ipv4 != null &&
            ipv4["from"] === fromZone &&
            ipv4["to"] === toZone &&
            ipv4["name"] === name
          );
        },
      });
      return accessRuleFromApiResponse(normalized);
    } catch (err) {
      if (err instanceof NotFoundError) {
        // fall through
      } else if (err instanceof SonicWallHTTPError && err.statusCode === 404) {
        // fall through
      } else {
        throw err;
      }
    }
    const rules = await this.list();
    for (const rule of rules) {
      if (rule.fromZone === fromZone && rule.toZone === toZone && rule.name === name) {
        return rule;
      }
    }
    throw new NotFoundError(
      `Access rule not found: ${fromZone}->${toZone}:${name}`
    );
  }

  async create(rule: AccessRule): Promise<AccessRule> {
    const payload = accessRuleToApiDict(rule);
    try {
      await this._post(BASE, payload);
    } catch (err) {
      if (!isSchemaArrayError(err)) throw err;
      await this._post(BASE, toCollectionPayload(rule));
    }
    if (rule.name) {
      try {
        return await this.get(rule.fromZone, rule.toZone, rule.name);
      } catch {
        console.warn("Create succeeded but access-rule get failed; returning input rule");
      }
    }
    return rule;
  }

  async update(
    fromZone: string,
    toZone: string,
    name: string,
    rule: AccessRule
  ): Promise<AccessRule> {
    const fromEnc = encodeURIComponent(fromZone);
    const toEnc = encodeURIComponent(toZone);
    const nameEnc = encodeURIComponent(name);
    const path = `${BASE}/from/${fromEnc}/to/${toEnc}/name/${nameEnc}`;
    const payload = accessRuleToApiDict(rule);
    try {
      await this._put(path, payload);
    } catch (err) {
      if (!isSchemaArrayError(err)) throw err;
      await this._put(path, toCollectionPayload(rule));
    }
    const effectiveName = rule.name ?? name;
    try {
      return await this.get(rule.fromZone, rule.toZone, effectiveName);
    } catch {
      console.warn("Update succeeded but access-rule get failed; returning input rule");
      return rule;
    }
  }

  async delete(fromZone: string, toZone: string, name: string): Promise<void> {
    const fromEnc = encodeURIComponent(fromZone);
    const toEnc = encodeURIComponent(toZone);
    const nameEnc = encodeURIComponent(name);
    await this._delete(`${BASE}/from/${fromEnc}/to/${toEnc}/name/${nameEnc}`);
  }

  async insertBefore(rule: AccessRule, beforeName: string): Promise<AccessRule> {
    try {
      const target = await this.get(rule.fromZone, rule.toZone, beforeName);
      if (!target.priority.auto && target.priority.value != null) {
        rule = {
          ...rule,
          priority: { auto: false, value: target.priority.value },
        };
      }
    } catch {
      // fall through to regular create
    }
    return this.create(rule);
  }

  async insertAfter(rule: AccessRule, afterName: string): Promise<AccessRule> {
    try {
      const target = await this.get(rule.fromZone, rule.toZone, afterName);
      if (!target.priority.auto && target.priority.value != null) {
        rule = {
          ...rule,
          priority: { auto: false, value: target.priority.value + 1 },
        };
      }
    } catch {
      // fall through
    }
    return this.create(rule);
  }
}
