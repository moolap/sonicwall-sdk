/** Pure firmware limitation detection (no error-class imports). */

export type FirmwareLimitationReason =
  | "api_not_found"
  | "endpoint_incomplete"
  | "command_not_found"
  | "non_config_mode";

/** Return a short reason when SonicOS indicates a firmware/API limitation. */
export function firmwareLimitationReason(
  statusCode: number,
  message: string
): FirmwareLimitationReason | null {
  const msg = message.toLowerCase();
  if (msg.includes("api not found")) return "api_not_found";
  if (msg.includes("endpoint is incomplete") || (statusCode === 400 && msg.includes("incomplete"))) {
    return "endpoint_incomplete";
  }
  if (msg.includes("command") && msg.includes("not found")) return "command_not_found";
  if (statusCode === 405 && msg.includes("non config mode")) return "non_config_mode";
  return null;
}
