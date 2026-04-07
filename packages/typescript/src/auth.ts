/**
 * AuthManager — session-based auth for SonicOS REST API.
 *
 * Uses a promise-chain mutex to prevent concurrent re-authentication storms.
 * The SonicOS session cookie (smngsess) is stored and injected into requests
 * via ky's beforeRequest hooks.
 */

import type { BeforeRequestHook, KyInstance, Options } from "ky";
import { AuthenticationError, SessionExpiredError } from "./errors.ts";

export class AuthManager {
  private sessionCookie: string | null = null;
  private authenticated = false;
  /** Mutex: a promise that resolves when the current re-auth is complete. */
  private authPromise: Promise<void> | null = null;

  constructor(
    private readonly baseUrl: string,
    private readonly username: string,
    private readonly password: string
  ) {}

  get isAuthenticated(): boolean {
    return this.authenticated && this.sessionCookie !== null;
  }

  async authenticate(ky: KyInstance): Promise<void> {
    const credentials = btoa(`${this.username}:${this.password}`);
    const response = await ky
      .post("auth", {
        headers: {
          Authorization: `Basic ${credentials}`,
          "Content-Type": "application/json",
        },
        body: "{}",
        // Skip auth hook during auth itself
        hooks: { beforeRequest: [] },
      })
      .json<Record<string, unknown>>();

    const respWithHeaders = await ky.post("auth", {
      headers: {
        Authorization: `Basic ${credentials}`,
        "Content-Type": "application/json",
      },
      body: "{}",
      hooks: { beforeRequest: [] },
    });

    // Extract cookie from Set-Cookie header
    const setCookie = respWithHeaders.headers.get("set-cookie") ?? "";
    const match = /smngsess=([^;]+)/.exec(setCookie);
    if (!match) {
      throw new AuthenticationError(
        200,
        "Authentication succeeded but no smngsess cookie was returned"
      );
    }

    this.sessionCookie = match[1] ?? null;
    this.authenticated = true;
  }

  /** Authenticate once; concurrent callers share the same promise. */
  async ensureAuthenticated(ky: KyInstance): Promise<void> {
    if (this.isAuthenticated) return;

    if (this.authPromise) {
      // Another caller is already authenticating — wait for it
      return this.authPromise;
    }

    this.authPromise = this._doAuthenticate(ky).finally(() => {
      this.authPromise = null;
    });

    return this.authPromise;
  }

  private async _doAuthenticate(ky: KyInstance): Promise<void> {
    const credentials = btoa(`${this.username}:${this.password}`);
    const response = await ky.post("auth", {
      headers: {
        Authorization: `Basic ${credentials}`,
        "Content-Type": "application/json",
      },
      body: "{}",
      hooks: { beforeRequest: [] },
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new AuthenticationError(
        response.status,
        "Authentication failed",
        body as Record<string, unknown>
      );
    }

    // Extract session cookie from Set-Cookie header
    const setCookie = response.headers.get("set-cookie") ?? "";
    const match = /smngsess=([^;]+)/.exec(setCookie);
    if (!match?.[1]) {
      throw new AuthenticationError(
        200,
        "Authentication succeeded but no smngsess cookie was returned"
      );
    }

    this.sessionCookie = match[1];
    this.authenticated = true;
  }

  async reauthenticate(ky: KyInstance): Promise<void> {
    // Reset state and re-authenticate
    this.sessionCookie = null;
    this.authenticated = false;
    // Wait for any in-flight auth to complete first
    if (this.authPromise) {
      await this.authPromise.catch(() => undefined);
    }
    this.authPromise = this._doAuthenticate(ky).finally(() => {
      this.authPromise = null;
    });
    return this.authPromise;
  }

  async logout(ky: KyInstance): Promise<void> {
    if (!this.isAuthenticated) return;
    try {
      await ky.delete("auth", {
        headers: { Cookie: `smngsess=${this.sessionCookie}` },
        hooks: { beforeRequest: [] },
      });
    } catch {
      // Best-effort logout
    } finally {
      this.sessionCookie = null;
      this.authenticated = false;
    }
  }

  /** ky beforeRequest hook that injects the session cookie. */
  get beforeRequestHook(): BeforeRequestHook {
    return (request) => {
      if (this.sessionCookie) {
        request.headers.set("Cookie", `smngsess=${this.sessionCookie}`);
      }
    };
  }

  getSessionCookie(): string | null {
    return this.sessionCookie;
  }

  isSessionExpiredResponse(body: Record<string, unknown>): boolean {
    const info = (body as { status?: { info?: Array<{ code?: number }> } }).status?.info;
    return (
      Array.isArray(info) &&
      info.some((i) => i.code === SessionExpiredError.SESSION_EXPIRED_CODE)
    );
  }
}