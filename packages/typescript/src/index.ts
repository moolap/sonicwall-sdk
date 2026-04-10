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

export {
  AccessRuleActionSchema,
  RuleAddressSchema,
  RuleServiceSchema,
  RulePrioritySchema,
  AccessRuleSchema,
  accessRuleToApiDict,
  accessRuleFromApiResponse,
} from "./models/accessRule.ts";
export type {
  AccessRule,
  AccessRuleAction,
  RuleAddress,
  RuleService,
  RulePriority,
} from "./models/accessRule.ts";

export {
  NatPolicySchema,
  natPolicyToApiDict,
  natPolicyFromApiResponse,
  natPolicyFirmwareCollectionPayload,
} from "./models/natPolicy.ts";
export type { NatPolicy } from "./models/natPolicy.ts";

export {
  PortRangeSchema,
  IcmpSpecSchema,
  ServiceProtocolSchema,
  ServiceObjectSchema,
  serviceObjectToApiDict,
  serviceObjectFromApiResponse,
  firmwareServiceObjectCollectionPayload,
} from "./models/serviceObject.ts";
export type {
  PortRange,
  IcmpSpec,
  ServiceProtocol,
  ServiceObject,
} from "./models/serviceObject.ts";

export {
  IPAssignmentSchema,
  InterfaceSchema,
  interfaceFromApiResponse,
} from "./models/interface.ts";
export type { Interface, IPAssignment } from "./models/interface.ts";

export { DhcpLeaseSchema, dhcpLeaseFromApiResponse } from "./models/dhcpLease.ts";
export type { DhcpLease } from "./models/dhcpLease.ts";

// Resources
export { AddressObjectsResource } from "./resources/addressObjects.ts";
export { AccessRulesResource } from "./resources/accessRules.ts";
export { NatPoliciesResource } from "./resources/natPolicies.ts";
export { ServiceObjectsResource } from "./resources/serviceObjects.ts";
export { InterfacesResource } from "./resources/interfaces.ts";
export { DhcpResource } from "./resources/dhcp.ts";