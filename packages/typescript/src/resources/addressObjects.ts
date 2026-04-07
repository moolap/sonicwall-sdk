/**
 * AddressObjectsResource — CRUD for SonicOS IPv4 address objects.
 */

import type { SonicWallClient } from "../client.ts";
import { NotFoundError } from "../errors.ts";
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
    return this._list(BASE, "address_objects", fromApiResponse);
  }

  /** Get a single address object by name. */
  async get(name: string): Promise<AddressObject> {
    const encoded = encodeURIComponent(name);
    const response = await this._get<Record<string, unknown>>(
      `${BASE}/name/${encoded}`
    );
    return fromApiResponse(response);
  }

  /** Create a new IPv4 address object. */
  async create(obj: AddressObject): Promise<AddressObject> {
    await this._post(`${BASE}`, toApiDict(obj));
    return this.get(obj.name);
  }

  /** Update an existing address object. */
  async update(name: string, obj: AddressObject): Promise<AddressObject> {
    const encoded = encodeURIComponent(name);
    await this._put(`${BASE}/name/${encoded}`, toApiDict(obj));
    return this.get(obj.name);
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
}