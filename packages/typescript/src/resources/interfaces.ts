/**
 * InterfacesResource — read-only SonicOS network interfaces.
 */

import type { SonicWallClient } from "../client.ts";
import { interfaceFromApiResponse, type Interface } from "../models/interface.ts";
import { BaseResource } from "./base.ts";

const BASE = "interfaces";

export class InterfacesResource extends BaseResource {
  constructor(client: SonicWallClient) {
    super(client);
  }

  async list(): Promise<Interface[]> {
    return this._list(
      BASE,
      "interfaces",
      (item) => interfaceFromApiResponse(item as Record<string, unknown>),
      true
    );
  }

  async get(name: string): Promise<Interface> {
    const enc = encodeURIComponent(name);
    const response = await this._get<Record<string, unknown>>(`${BASE}/name/${enc}`);
    return interfaceFromApiResponse(response);
  }
}
