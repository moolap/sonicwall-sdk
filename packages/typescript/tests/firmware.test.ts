import { describe, expect, it } from "vitest";
import { firmwareLimitationReason, isFirmwareUnsupportedError } from "../src/firmware.ts";
import {
  SonicWallHTTPError,
  UnsupportedEndpointError,
  raiseForSonicOSBody,
} from "../src/errors.ts";

describe("firmwareLimitationReason", () => {
  it.each([
    [404, "API not found", "api_not_found"],
    [400, "API endpoint is incomplete", "endpoint_incomplete"],
    [400, "incomplete", "endpoint_incomplete"],
    [404, "command xyz not found", "command_not_found"],
    [405, "Non config mode", "non_config_mode"],
    [500, "Internal server error", null],
  ] as const)("classifies %i %s as %s", (statusCode, message, expected) => {
    expect(firmwareLimitationReason(statusCode, message)).toBe(expected);
  });
});

describe("UnsupportedEndpointError", () => {
  it("is raised for endpoint incomplete responses", () => {
    expect(() =>
      raiseForSonicOSBody(400, {
        status: {
          success: false,
          info: [{ code: 400, message: "API endpoint is incomplete" }],
        },
      })
    ).toThrow(UnsupportedEndpointError);

    try {
      raiseForSonicOSBody(400, {
        status: {
          success: false,
          info: [{ code: 400, message: "API endpoint is incomplete" }],
        },
      });
    } catch (err) {
      expect(err).toBeInstanceOf(UnsupportedEndpointError);
      expect((err as UnsupportedEndpointError).reason).toBe("endpoint_incomplete");
    }
  });

  it("isFirmwareUnsupportedError detects typed errors", () => {
    const exc = new UnsupportedEndpointError(400, "API endpoint is incomplete", "endpoint_incomplete");
    expect(isFirmwareUnsupportedError(exc)).toBe(true);
    expect(isFirmwareUnsupportedError(new SonicWallHTTPError(500, "fail"))).toBe(false);
  });
});
