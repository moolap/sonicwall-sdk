/**
 * AuthManager — SonicOS session auth (Digest + bearer or Basic + cookie).
 */

import type { BeforeRequestHook } from "ky";
import { AuthenticationError, SessionExpiredError } from "./errors.ts";
import {
  buildDigestAuthHeader,
  extractBearerToken,
  pickAuthIntChallenge,
} from "./digest.ts";

type AuthMode = "bearer" | "cookie";

export class AuthManager {
  private sessionCookie: string | null = null;
  private bearerToken: string | null = null;
  private authMode: AuthMode | null = null;
  private authenticated = false;
  private authPromise: Promise<void> | null = null;

  constructor(
    private readonly baseUrl: string,
    private readonly username: string,
    private readonly password: string
  ) {}

  get isAuthenticated(): boolean {
    return this.authenticated && (this.bearerToken !== null || this.sessionCookie !== null);
  }

  async ensureAuthenticated(): Promise<void> {
    if (this.isAuthenticated) return;

    if (this.authPromise) {
      return this.authPromise;
    }

    this.authPromise = this.authenticate().finally(() => {
      this.authPromise = null;
    });

    return this.authPromise;
  }

  async reauthenticate(): Promise<void> {
    this.sessionCookie = null;
    this.bearerToken = null;
    this.authMode = null;
    this.authenticated = false;
    if (this.authPromise) {
      await this.authPromise.catch(() => undefined);
    }
    this.authPromise = this.authenticate().finally(() => {
      this.authPromise = null;
    });
    return this.authPromise;
  }

  async logout(): Promise<void> {
    if (!this.isAuthenticated) return;
    const authUrl = `${this.baseUrl}auth`;
    const headers: Record<string, string> = { Accept: "application/json" };
    if (this.authMode === "bearer" && this.bearerToken) {
      headers.Authorization = `Bearer ${this.bearerToken}`;
    } else if (this.sessionCookie) {
      headers.Cookie = `smngsess=${this.sessionCookie}`;
    }
    try {
      await fetch(authUrl, { method: "DELETE", headers });
    } catch {
      // best effort
    } finally {
      this.sessionCookie = null;
      this.bearerToken = null;
      this.authMode = null;
      this.authenticated = false;
    }
  }

  get beforeRequestHook(): BeforeRequestHook {
    return (request) => {
      if (this.authMode === "bearer" && this.bearerToken) {
        request.headers.set("Authorization", `Bearer ${this.bearerToken}`);
      } else if (this.sessionCookie) {
        request.headers.set("Cookie", `smngsess=${this.sessionCookie}`);
      }
    };
  }

  getSessionCookie(): string | null {
    return this.sessionCookie;
  }

  getBearerToken(): string | null {
    return this.bearerToken;
  }

  isSessionExpiredResponse(body: Record<string, unknown>): boolean {
    const info = (body as { status?: { info?: Array<{ code?: number }> } }).status?.info;
    return (
      Array.isArray(info) &&
      info.some((i) => i.code === SessionExpiredError.SESSION_EXPIRED_CODE)
    );
  }

  private async authenticate(): Promise<void> {
    const authUrl = `${this.baseUrl}auth`;
    const bodyText = "{}";
    const baseHeaders = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };

    const challengeResp = await fetch(authUrl, {
      method: "POST",
      headers: baseHeaders,
      body: bodyText,
    });

    if (challengeResp.status === 401) {
      const digestHeaders: string[] = [];
      challengeResp.headers.forEach((value, key) => {
        if (key.toLowerCase() === "www-authenticate") {
          digestHeaders.push(value);
        }
      });

      const challenge = pickAuthIntChallenge(digestHeaders);
      if (challenge) {
        await this.authenticateDigest(authUrl, bodyText, baseHeaders, challenge);
        return;
      }
      await this.authenticateBasicCookie(authUrl, bodyText, baseHeaders);
      return;
    }

    if (!challengeResp.ok) {
      const responseBody = await challengeResp.json().catch(() => ({}));
      throw new AuthenticationError(
        challengeResp.status,
        `Authentication failed with status ${challengeResp.status}`,
        responseBody as Record<string, unknown>
      );
    }

    await this.consumeAuthSuccess(challengeResp);
  }

  private async authenticateDigest(
    authUrl: string,
    bodyText: string,
    baseHeaders: Record<string, string>,
    challenge: ReturnType<typeof pickAuthIntChallenge>
  ): Promise<void> {
    if (!challenge) {
      throw new AuthenticationError(401, "Missing Digest challenge");
    }
    const body = Buffer.from(bodyText, "utf8");
    const authHeader = buildDigestAuthHeader(
      "POST",
      authUrl,
      body,
      this.username,
      this.password,
      challenge
    );
    const response = await fetch(authUrl, {
      method: "POST",
      headers: { ...baseHeaders, Authorization: authHeader },
      body: bodyText,
    });

    if (response.status === 401) {
      const responseBody = await response.json().catch(() => ({}));
      throw new AuthenticationError(
        401,
        "Authentication failed: invalid username or password",
        responseBody as Record<string, unknown>
      );
    }
    if (!response.ok) {
      const responseBody = await response.json().catch(() => ({}));
      throw new AuthenticationError(
        response.status,
        `Authentication failed with status ${response.status}`,
        responseBody as Record<string, unknown>
      );
    }
    await this.consumeAuthSuccess(response);
  }

  private async authenticateBasicCookie(
    authUrl: string,
    bodyText: string,
    baseHeaders: Record<string, string>
  ): Promise<void> {
    const credentials = Buffer.from(`${this.username}:${this.password}`).toString("base64");
    const response = await fetch(authUrl, {
      method: "POST",
      headers: { ...baseHeaders, Authorization: `Basic ${credentials}` },
      body: bodyText,
    });

    if (response.status === 401) {
      const responseBody = await response.json().catch(() => ({}));
      throw new AuthenticationError(
        401,
        "Authentication failed: invalid username or password",
        responseBody as Record<string, unknown>
      );
    }
    if (!response.ok) {
      const responseBody = await response.json().catch(() => ({}));
      throw new AuthenticationError(
        response.status,
        "Authentication failed",
        responseBody as Record<string, unknown>
      );
    }
    await this.consumeAuthSuccess(response);
  }

  private async consumeAuthSuccess(response: Response): Promise<void> {
    const responseBody = await response.json().catch(() => ({}));
    const token = extractBearerToken(responseBody);
    if (token) {
      this.bearerToken = token;
      this.sessionCookie = null;
      this.authMode = "bearer";
      this.authenticated = true;
      return;
    }

    const setCookie = response.headers.get("set-cookie") ?? "";
    const match = /smngsess=([^;]+)/.exec(setCookie);
    if (match?.[1]) {
      this.sessionCookie = match[1];
      this.bearerToken = null;
      this.authMode = "cookie";
      this.authenticated = true;
      return;
    }

    throw new AuthenticationError(
      200,
      "Authentication succeeded but no bearer_token or smngsess cookie was returned",
      responseBody as Record<string, unknown>
    );
  }
}
