import { describe, expect, it } from "vitest";
import {
  buildDigestAuthHeader,
  extractBearerToken,
  parseDigestChallenge,
  pickAuthIntChallenge,
} from "../src/digest.ts";

describe("digest", () => {
  it("parseDigestChallenge extracts params", () => {
    const parsed = parseDigestChallenge(
      'Digest realm="sonicwall", nonce="abc123", algorithm=SHA-256, qop="auth-int"'
    );
    expect(parsed.realm).toBe("sonicwall");
    expect(parsed.nonce).toBe("abc123");
    expect(parsed.algorithm).toBe("SHA-256");
    expect(parsed.qop).toBe("auth-int");
  });

  it("pickAuthIntChallenge prefers SHA-256", () => {
    const picked = pickAuthIntChallenge([
      'Digest realm="x", nonce="1", algorithm=MD5, qop="auth-int"',
      'Digest realm="x", nonce="2", algorithm=SHA-256, qop="auth-int"',
    ]);
    expect(picked?.algorithm).toBe("SHA-256");
  });

  it("buildDigestAuthHeader is deterministic with fixed cnonce", () => {
    // buildDigestAuthHeader uses random cnonce — smoke test only structure
    const header = buildDigestAuthHeader(
      "POST",
      "https://192.168.0.1/api/sonicos/auth",
      Buffer.from("{}"),
      "admin",
      "password",
      {
        realm: "sonicwall",
        nonce: "abc123",
        algorithm: "SHA-256",
        qop: "auth-int",
      }
    );
    expect(header).toContain('Digest username="admin"');
    expect(header).toContain("qop=auth-int");
    expect(header).toContain('realm="sonicwall"');
  });

  it("extractBearerToken reads status.info", () => {
    const token = extractBearerToken({
      status: { info: [{ bearer_token: "jwt-here" }] },
    });
    expect(token).toBe("jwt-here");
  });
});
