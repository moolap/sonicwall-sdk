/**
 * SonicWallClient — main entry point for the TypeScript SDK.
 */

import ky, { HTTPError } from "ky";
import type { KyInstance } from "ky";
import { AuthManager } from "./auth.ts";
import {
  AuthenticationError,
  AuthorizationError,
  CommitError,
  ConflictError,
  ConnectionError,
  NotFoundError,
  RollbackError,
  SessionExpiredError,
  SonicWallHTTPError,
  raiseForSonicOSBody,
} from "./errors.ts";
import type { SonicOSResponseBody } from "./errors.ts";
import { AccessRulesResource } from "./resources/accessRules.ts";
import { AddressObjectsResource } from "./resources/addressObjects.ts";
import { DhcpResource } from "./resources/dhcp.ts";
import { InterfacesResource } from "./resources/interfaces.ts";
import { NatPoliciesResource } from "./resources/natPolicies.ts";
import { ServiceObjectsResource } from "./resources/serviceObjects.ts";

export interface SonicWallClientOptions {
  /** SonicWall management IP or hostname. */
  host: string;
  /** Management username. */
  username: string;
  /** Management password. */
  password: string;
  /** Disable SSL certificate verification (default: true — verification disabled). */
  verifySsl?: boolean;
  /** Request timeout in milliseconds (default: 30000). */
  timeout?: number;
}

export class SonicWallClient {
  private readonly auth: AuthManager;
  readonly _ky: KyInstance;

  private _addressObjects: AddressObjectsResource | undefined;
  private _accessRules: AccessRulesResource | undefined;
  private _natPolicies: NatPoliciesResource | undefined;
  private _serviceObjects: ServiceObjectsResource | undefined;
  private _interfaces: InterfacesResource | undefined;
  private _dhcp: DhcpResource | undefined;
  private _pendingDepth = 0;

  constructor(private readonly options: SonicWallClientOptions) {
    const baseUrl = `${this.normalizeBaseHost(options.host)}/api/sonicos/`;
    this.auth = new AuthManager(baseUrl, options.username, options.password);

    this._ky = ky.create({
      prefixUrl: baseUrl,
      timeout: options.timeout ?? 30000,
      retry: 0,
      // Node.js fetch does not have a direct `rejectUnauthorized` option via ky
      // For SSL bypass in Node >=18 pass a custom dispatcher or use fetch with agent.
      // The option below is handled in node environments via the dispatcher.
      hooks: {
        beforeRequest: [this.auth.beforeRequestHook],
        afterResponse: [
          async (_request, _options, response) => {
            // On 401, the retry logic in request() handles re-auth.
            return response;
          },
        ],
      },
    });
  }

  // --- Lifecycle ---

  async connect(): Promise<void> {
    await this.auth.ensureAuthenticated();
  }

  async disconnect(): Promise<void> {
    await this.auth.logout();
  }

  // --- Commit / Rollback ---

  async commit(): Promise<void> {
    try {
      await this.request<SonicOSResponseBody>("POST", "config/pending");
    } catch (err) {
      throw new CommitError(
        `Failed to commit pending configuration: ${err}`,
        err instanceof Error ? err : undefined
      );
    }
  }

  async rollback(): Promise<void> {
    try {
      await this.request<SonicOSResponseBody>("DELETE", "config/pending");
    } catch (err) {
      throw new RollbackError(
        `Failed to roll back pending configuration: ${err}`,
        err instanceof Error ? err : undefined
      );
    }
  }

  /**
   * Execute an async function within a pending-config transaction.
   * Commits on success, rolls back on any error.
   */
  async transaction<T>(fn: () => Promise<T>): Promise<T> {
    this._pendingDepth++;
    const isOutermost = this._pendingDepth === 1;
    try {
      const result = await fn();
      if (isOutermost) {
        await this.commit();
      }
      return result;
    } catch (err) {
      if (isOutermost) {
        try {
          await this.rollback();
        } catch (rollbackErr) {
          // Log rollback failure but throw original error
          console.error("Rollback failed:", rollbackErr);
        }
      }
      throw err;
    } finally {
      this._pendingDepth--;
    }
  }

  // --- Resources ---

  get addressObjects(): AddressObjectsResource {
    if (!this._addressObjects) {
      this._addressObjects = new AddressObjectsResource(this);
    }
    return this._addressObjects;
  }

  get accessRules(): AccessRulesResource {
    if (!this._accessRules) {
      this._accessRules = new AccessRulesResource(this);
    }
    return this._accessRules;
  }

  get natPolicies(): NatPoliciesResource {
    if (!this._natPolicies) {
      this._natPolicies = new NatPoliciesResource(this);
    }
    return this._natPolicies;
  }

  get serviceObjects(): ServiceObjectsResource {
    if (!this._serviceObjects) {
      this._serviceObjects = new ServiceObjectsResource(this);
    }
    return this._serviceObjects;
  }

  get interfaces(): InterfacesResource {
    if (!this._interfaces) {
      this._interfaces = new InterfacesResource(this);
    }
    return this._interfaces;
  }

  get dhcp(): DhcpResource {
    if (!this._dhcp) {
      this._dhcp = new DhcpResource(this);
    }
    return this._dhcp;
  }

  // --- Internal request method (used by resources) ---

  async request<T>(
    method: string,
    path: string,
    options: { json?: unknown; searchParams?: Record<string, string> } = {}
  ): Promise<T> {
    await this.auth.ensureAuthenticated();

    const doRequest = async (): Promise<T> => {
      const kyOptions: Record<string, unknown> = {
        method,
        headers: {
          Accept: "application/json",
          ...(options.json !== undefined
            ? { "Content-Type": "application/json" }
            : {}),
        },
      };
      if (options.json !== undefined) {
        kyOptions["json"] = options.json;
      }
      if (options.searchParams) {
        kyOptions["searchParams"] = options.searchParams;
      }

      const response = await this._ky(path, kyOptions as Parameters<KyInstance>[1]);
      const body = (await response.json()) as SonicOSResponseBody;

      // Check for SonicOS-level errors even on HTTP 200
      raiseForSonicOSBody(response.status, body);

      return body as T;
    };

    try {
      return await doRequest();
    } catch (err) {
      if (err instanceof SessionExpiredError || this._is401(err)) {
        // Re-authenticate once and retry
        await this.auth.reauthenticate();
        try {
          return await doRequest();
        } catch (retryErr) {
          throw this._wrapError(retryErr);
        }
      }
      throw this._wrapError(err);
    }
  }

  private _is401(err: unknown): boolean {
    return err instanceof HTTPError && err.response.status === 401;
  }

  private _wrapError(err: unknown): Error {
    if (
      err instanceof SonicWallHTTPError ||
      err instanceof CommitError ||
      err instanceof RollbackError ||
      err instanceof ConnectionError
    ) {
      return err;
    }
    if (err instanceof HTTPError) {
      const status = err.response.status;
      if (status === 401) return new AuthenticationError(401, "Unauthorized");
      if (status === 403) return new AuthorizationError();
      if (status === 404) return new NotFoundError();
      if (status === 409) return new ConflictError();
      return new SonicWallHTTPError(status, err.message);
    }
    if (err instanceof TypeError && err.message.includes("fetch")) {
      return new ConnectionError(`Network error: ${err.message}`);
    }
    if (err instanceof Error) return err;
    return new Error(String(err));
  }

  private normalizeBaseHost(host: string): string {
    const trimmed = host.trim().replace(/\/+$/, "");
    if (/^https?:\/\//i.test(trimmed)) {
      return trimmed;
    }
    return `https://${trimmed}`;
  }
}