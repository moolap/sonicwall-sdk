/** Firmware capability detection helpers. */

import {
  SonicWallError,
  SonicWallHTTPError,
  UnsupportedEndpointError,
} from "./errors.ts";
import { firmwareLimitationReason } from "./firmwareReason.ts";

export type { FirmwareLimitationReason } from "./firmwareReason.ts";
export { firmwareLimitationReason } from "./firmwareReason.ts";

/** True when err reflects a known firmware/API limitation (not an SDK bug). */
export function isFirmwareUnsupportedError(err: unknown): boolean {
  if (err instanceof UnsupportedEndpointError) return true;
  if (err instanceof SonicWallHTTPError) {
    if (firmwareLimitationReason(err.statusCode, err.message) !== null) return true;
    const sonicosMsg = err.sonicosMessage ?? "";
    return firmwareLimitationReason(err.statusCode, sonicosMsg) !== null;
  }
  if (err instanceof SonicWallError) {
    return firmwareLimitationReason(0, err.message) !== null;
  }
  return false;
}
