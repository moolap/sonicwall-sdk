/**
 * AddressObjectsResource — CRUD for SonicOS IPv4 address objects.
 */

import type { SonicWallClient } from "../client.ts";
import { NotFoundError, SonicWallHTTPError } from "../errors.ts";
import {
  fromApiResponse,
  toApiDict,
  type AddressObject,
} from "../models/addressObject.ts";
import { BaseResource } from "./base.ts";

const BASE = "address-objects/ipv4";

export class AddressObjectsResource extends BaseResource {
  constructor(client: SonicWallClient) {
    super(client);
  }

  /** List all IPv4 address objects. */
  async list(): Promise<AddressObject[]> {
    return this._list(BASE, "address_objects", fromApiResponse, true);
  }

  /** Get a single address object by name. */
  async get(name: string): Promise<AddressObject> {
    const encoded = encodeURIComponent(name);
    const response = await this._get<Record<string, unknown>>(
      `${BASE}/name/${encoded}`
    );
    return fromApiResponse(this.normalizeGetResponse(response, name));
  }

  /** Create a new IPv4 address object. */
  async create(obj: AddressObject): Promise<AddressObject> {
    try {
      await this._post(`${BASE}`, toApiDict(obj));
    } catch (err) {
      if (
        err instanceof SonicWallHTTPError &&
        err.statusCode === 400 &&
        /schema validation error/i.test(err.message) &&
        /address_objects/i.test(err.message)
      ) {
        const single = toApiDict(obj) as unknown as { address_object: unknown };
        await this._post(`${BASE}`, { address_objects: [single.address_object] });
      } else {
        throw err;
      }
    }
    try {
      return await this.get(obj.name);
    } catch {
      return obj;
    }
  }

  /** Update an existing address object. */
  async update(name: string, obj: AddressObject): Promise<AddressObject> {
    const encoded = encodeURIComponent(name);
    try {
      await this._put(`${BASE}/name/${encoded}`, toApiDict(obj));
    } catch (err) {
      if (
        err instanceof SonicWallHTTPError &&
        err.statusCode === 400 &&
        /schema validation error/i.test(err.message) &&
        /address_objects/i.test(err.message)
      ) {
        const single = toApiDict(obj) as unknown as { address_object: unknown };
        await this._put(`${BASE}/name/${encoded}`, { address_objects: [single.address_object] });
      } else {
        throw err;
      }
    }
    try {
      return await this.get(obj.name);
    } catch {
      return obj;
    }
  }

  /** Delete an address object by name. */
  async delete(name: string): Promise<void> {
    const encoded = encodeURIComponent(name);
    await this._delete(`${BASE}/name/${encoded}`);
  }

  /**
   * Create or update an address object (upsert).
   *
   * @returns [object, created] — created is true if newly created, false if updated.
   */
  async ensure(obj: AddressObject): Promise<[AddressObject, boolean]> {
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

  private normalizeGetResponse(
    response: Record<string, unknown>,
    expectedName: string
  ): Record<string, unknown> {
    const items = response["address_objects"];
    if (!Array.isArray(items)) return response;
    for (const item of items) {
      if (
        item &&
        typeof item === "object" &&
        "ipv4" in (item as Record<string, unknown>)
      ) {
        const ipv4 = (item as Record<string, unknown>)["ipv4"] as Record<string, unknown>;
        if (ipv4?.["name"] === expectedName) {
          return { address_object: { ipv4 } };
        }
      }
    }
    return response;
  }
}