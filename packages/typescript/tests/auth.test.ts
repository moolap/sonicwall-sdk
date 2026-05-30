import { beforeEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { AuthManager } from "../src/auth.ts";
import { BASE } from "./mocks/handlers.ts";
import { server } from "./mocks/server.ts";

describe("AuthManager digest + bearer", () => {
  let authCallCount: number;

  beforeEach(() => {
    authCallCount = 0;
  });

  it("authenticates with Digest auth-int and stores bearer token", async () => {
    server.use(
      http.post(`${BASE}/auth`, () => {
        authCallCount += 1;
        if (authCallCount === 1) {
          return new HttpResponse(
            JSON.stringify({
              status: { success: false, info: [{ code: 401, message: "Unauthorized" }] },
            }),
            {
              status: 401,
              headers: {
                "WWW-Authenticate":
                  'Digest realm="sonicwall", nonce="abc123", algorithm=SHA-256, qop="auth-int"',
              },
            }
          );
        }
        return HttpResponse.json({
          status: {
            success: true,
            info: [{ bearer_token: "test-bearer-token" }],
          },
        });
      })
    );

    const auth = new AuthManager(`${BASE}/`, "admin", "password");
    await auth.ensureAuthenticated({} as never);
    expect(auth.getBearerToken()).toBe("test-bearer-token");
    expect(auth.getSessionCookie()).toBeNull();
  });

  it("falls back to cookie auth when no auth-int challenge", async () => {
    server.use(
      http.post(`${BASE}/auth`, ({ request }) => {
        authCallCount += 1;
        if (authCallCount === 1) {
          return new HttpResponse(null, { status: 401 });
        }
        const authHeader = request.headers.get("authorization") ?? "";
        expect(authHeader.startsWith("Basic ")).toBe(true);
        return new HttpResponse(JSON.stringify({ status: { success: true, info: [] } }), {
          status: 200,
          headers: { "Set-Cookie": "smngsess=cookie-value; Path=/" },
        });
      })
    );

    const auth = new AuthManager(`${BASE}/`, "admin", "password");
    await auth.ensureAuthenticated({} as never);
    expect(auth.getSessionCookie()).toBe("cookie-value");
  });
});
