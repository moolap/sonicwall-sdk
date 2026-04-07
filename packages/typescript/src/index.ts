/**
 * @sonicwall/sdk — TypeScript SDK for the SonicOS REST API.
 *
 * @example
 * ```typescript
 * import { SonicWallClient } from "@sonicwall/sdk";
 *
 * const client = new SonicWallClient({
 *   host: "192.168.1.1",
 *   username: "admin",
 *   password: "password",
 * });
 *
 * await client.connect();
 * const objects = await client.addressObjects.list();
 * await client.disconnect();
 * ```
 */

export { SonicWallClient } from "./client.ts";
export type { SonicWallClientOptions } from "./client.ts";

// Errors
export {
  SonicWallError,
  SonicWallHTTPError,
  AuthenticationError,
  AuthorizationError,
  SessionExpiredError,
  NotFoundError,
  ConflictError,
  CommitError,
  RollbackError,
  ConnectionError,
  SONICOS_CODE_NOT_FOUND,
  SONICOS_CODE_ALREADY_EXISTS,
} from "./errors.ts";
export type { SonicOSResponseBody, SonicOSStatusInfo } from "./errors.ts";

// Models
export {
  AddressObjectTypeSchema,
  AddressObjectSchema,
  toApiDict as addressObjectToApiDict,
  fromApiResponse as addressObjectFromApiResponse,
} from "./models/addressObject.ts";
export type { AddressObject, AddressObjectType } from "./models/addressObject.ts";

// Resources
export { AddressObjectsResource } from "./resources/addressObjects.ts";