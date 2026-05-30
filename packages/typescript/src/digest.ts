/**
 * SonicOS 7.x Digest auth-int helpers (mirrors Python _auth.py).
 */

import { createHash, randomBytes } from "node:crypto";

export type DigestChallenge = Record<string, string>;

const DIGEST_PARAM_RE = /(\w+)=(?:"([^"]*?)"|([^,\s]+))/g;

export function parseDigestChallenge(wwwAuth: string): DigestChallenge {
  const body = wwwAuth.trim().replace(/^[Dd]igest\s+/, "");
  const params: DigestChallenge = {};
  for (const match of body.matchAll(DIGEST_PARAM_RE)) {
    const key = match[1];
    const value = match[2] ?? match[3] ?? "";
    if (key) params[key] = value;
  }
  return params;
}

function challengePriority(challenge: DigestChallenge): number {
  const alg = (challenge.algorithm ?? "MD5").toUpperCase();
  if (alg === "SHA-256") return 0;
  if (alg === "SHA-256-SESS") return 1;
  return 2;
}

export function pickAuthIntChallenge(
  wwwAuthenticate: string[]
): DigestChallenge | null {
  const candidates: DigestChallenge[] = [];
  for (const value of wwwAuthenticate) {
    if (!value.toLowerCase().startsWith("digest")) continue;
    const parsed = parseDigestChallenge(value);
    if ((parsed.qop ?? "").includes("auth-int")) {
      candidates.push(parsed);
    }
  }
  if (candidates.length === 0) return null;
  return candidates.sort((a, b) => challengePriority(a) - challengePriority(b))[0] ?? null;
}

function hashString(algorithm: string, value: string): string {
  const upper = algorithm.toUpperCase();
  if (upper.includes("SHA-256")) {
    return createHash("sha256").update(value, "utf8").digest("hex");
  }
  return createHash("md5").update(value, "utf8").digest("hex");
}

function hashBytes(algorithm: string, value: Buffer): string {
  const upper = algorithm.toUpperCase();
  if (upper.includes("SHA-256")) {
    return createHash("sha256").update(value).digest("hex");
  }
  return createHash("md5").update(value).digest("hex");
}

export function buildDigestAuthHeader(
  method: string,
  url: string,
  body: Buffer,
  username: string,
  password: string,
  challenge: DigestChallenge
): string {
  const algorithm = (challenge.algorithm ?? "MD5").toUpperCase();
  const realm = challenge.realm ?? "";
  const nonce = challenge.nonce ?? "";
  const opaque = challenge.opaque ?? "";

  const parsed = new URL(url);
  const uri = parsed.pathname + parsed.search;

  const cnonce = randomBytes(8).toString("hex");
  const nc = "00000001";

  let ha1 = hashString(algorithm, `${username}:${realm}:${password}`);
  if (algorithm.includes("SESS")) {
    ha1 = hashString(algorithm, `${ha1}:${nonce}:${cnonce}`);
  }

  const ha2 = hashString(algorithm, `${method}:${uri}:${hashBytes(algorithm, body)}`);
  const response = hashString(algorithm, `${ha1}:${nonce}:${nc}:${cnonce}:auth-int:${ha2}`);

  let header =
    `Digest username="${username}", realm="${realm}", ` +
    `nonce="${nonce}", uri="${uri}", algorithm=${algorithm}, ` +
    `qop=auth-int, nc=${nc}, cnonce="${cnonce}", response="${response}"`;
  if (opaque) header += `, opaque="${opaque}"`;
  return header;
}

export function extractBearerToken(body: unknown): string | null {
  if (!body || typeof body !== "object") return null;
  const info = (body as { status?: { info?: Array<{ bearer_token?: string }> } }).status?.info;
  if (!Array.isArray(info)) return null;
  for (const item of info) {
    if (item?.bearer_token) return String(item.bearer_token);
  }
  return null;
}
