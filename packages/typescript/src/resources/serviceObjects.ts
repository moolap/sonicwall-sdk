/**
 * ServiceObjectsResource — CRUD for SonicOS service objects.
 */

import type { SonicWallClient } from "../client.ts";
import { NotFoundError, SonicWallHTTPError } from "../errors.ts";
import {
  firmwareServiceObjectCollectionPayload,
  serviceObjectFromApiResponse,
  serviceObjectToApiDict,
  type ServiceObject,
} from "../models/serviceObject.ts";
import { normalizeGetFromPlural } from "./normalize.ts";
import { BaseResource } from "./base.ts";

const BASE = "service-objects";

function toCollectionPayload(obj: ServiceObject): Record<string, unknown> {
  const single = serviceObjectToApiDict(obj) as { service_object?: unknown };
  return { service_objects: [single.service_object ?? single] };
}

function isSchemaArrayError(err: unknown): boolean {
  if (!(err instanceof SonicWallHTTPError) || err.statusCode !== 400) return false;
  const msg = err.message.toLowerCase();
  return (
    msg.includes("schema validation error") &&
    msg.includes("service_objects") &&
    msg.includes("expected '['")
  );
}

export class ServiceObjectsResource extends BaseResource {
  constructor(client: SonicWallClient) {
    super(client);
  }

  async list(): Promise<ServiceObject[]> {
    return this._list(
      BASE,
      "service_objects",
      (item) => serviceObjectFromApiResponse(item as Record<string, unknown>),
      true
    );
  }

  async get(name: string): Promise<ServiceObject> {
    const enc = encodeURIComponent(name);
    try {
      const response = await this._get<Record<string, unknown>>(`${BASE}/name/${enc}`);
      const normalized = normalizeGetFromPlural(response, {
        pluralKey: "service_objects",
        singularKey: "service_object",
        predicate: (item) => {
          const so = item["service_object"] as Record<string, unknown> | undefined;
          if (so && typeof so === "object" && so["name"] === name) return true;
          return item["name"] === name;
        },
      });
      return serviceObjectFromApiResponse(normalized);
    } catch (err) {
      if (!(err instanceof NotFoundError)) {
        if (!(err instanceof SonicWallHTTPError) || err.statusCode !== 404) {
          throw err;
        }
      }
    }
    for (const o of await this.list()) {
      if (o.name === name) return o;
    }
    throw new NotFoundError(`Service object not found: ${name}`);
  }

  async create(obj: ServiceObject): Promise<ServiceObject> {
    const payload = serviceObjectToApiDict(obj);
    try {
      await this._post(BASE, payload);
    } catch (err) {
      if (!isSchemaArrayError(err)) throw err;
      try {
        await this._post(BASE, toCollectionPayload(obj));
      } catch {
        await this._post(BASE, firmwareServiceObjectCollectionPayload(obj));
      }
    }
    try {
      return await this.get(obj.name);
    } catch {
      console.warn("Create succeeded but service object get failed; returning input");
      return obj;
    }
  }

  async update(name: string, obj: ServiceObject): Promise<ServiceObject> {
    const enc = encodeURIComponent(name);
    const path = `${BASE}/name/${enc}`;
    const payload = serviceObjectToApiDict(obj);
    try {
      await this._put(path, payload);
    } catch (err) {
      if (!isSchemaArrayError(err)) throw err;
      try {
        await this._put(path, toCollectionPayload(obj));
      } catch {
        await this._put(path, firmwareServiceObjectCollectionPayload(obj));
      }
    }
    try {
      return await this.get(obj.name);
    } catch {
      console.warn("Update succeeded but service object get failed; returning input");
      return obj;
    }
  }

  async delete(name: string): Promise<void> {
    const enc = encodeURIComponent(name);
    await this._delete(`${BASE}/name/${enc}`);
  }

  async ensure(obj: ServiceObject): Promise<[ServiceObject, boolean]> {
    try {
      await this.get(obj.name);
      const updated = await this.update(obj.name, obj);
      return [updated, false];
    } catch (err) {
      if (err instanceof NotFoundError) {
        const created = await this.create(obj);
        return [created, true];
      }
      throw err;
    }
  }
}
