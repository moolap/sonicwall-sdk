/**
 * BaseResource — shared HTTP helpers for all SonicOS resources.
 */

import type { SonicWallClient } from "../client.ts";
import type { SonicOSResponseBody } from "../errors.ts";

export abstract class BaseResource {
  constructor(protected readonly client: SonicWallClient) {}

  protected async _get<T>(path: string, params?: Record<string, string>): Promise<T> {
    return this.client.request<T>("GET", path, { searchParams: params });
  }

  protected async _post<T>(path: string, body: unknown): Promise<T> {
    return this.client.request<T>("POST", path, { json: body });
  }

  protected async _put<T>(path: string, body: unknown): Promise<T> {
    return this.client.request<T>("PUT", path, { json: body });
  }

  protected async _delete(path: string): Promise<void> {
    await this.client.request<SonicOSResponseBody>("DELETE", path);
  }

  /**
   * Fetch and unwrap a SonicOS list response.
   *
   * @param path - API path
   * @param listKey - Top-level key containing the array, e.g. "address_objects"
   * @param parse - Function to parse each item in the array
   */
  protected async _list<T>(
    path: string,
    listKey: string,
    parse: (item: Record<string, unknown>) => T
  ): Promise<T[]> {
    const response = await this._get<Record<string, unknown>>(path);
    const items = response[listKey];
    if (!Array.isArray(items)) return [];
    return items.map((item) => parse(item as Record<string, unknown>));
  }
}