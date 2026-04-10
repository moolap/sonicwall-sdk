/**
 * Tests for AddressObjectsResource.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { http, HttpResponse } from "msw";
import { SonicWallClient } from "../src/client.ts";
import { NotFoundError, ConflictError } from "../src/errors.ts";
import type { AddressObject } from "../src/models/addressObject.ts";
import { server } from "./mocks/server.ts";
import {
  BASE,
  ADDR_OBJ_HOST,
  makeSingleResponse,
  NOT_FOUND_RESPONSE,
  CONFLICT_RESPONSE,
} from "./mocks/handlers.ts";

function makeClient(): SonicWallClient {
  return new SonicWallClient({
    host: "192.168.1.1",
    username: "admin",
    password: "password",
  });
}

describe("AddressObjectsResource", () => {
  let client: SonicWallClient;

  beforeEach(async () => {
    client = makeClient();
    await client.connect();
  });

  afterEach(async () => {
    await client.disconnect();
  });

  describe("list()", () => {
    it("returns all address objects", async () => {
      const objects = await client.addressObjects.list();
      expect(objects).toHaveLength(2);
      expect(objects[0]?.name).toBe("my-server");
      expect(objects[0]?.type).toBe("host");
      expect(objects[0]?.host).toBe("10.0.0.100");
      expect(objects[1]?.name).toBe("internal-net");
      expect(objects[1]?.type).toBe("network");
    });

    it("returns empty array when no objects exist", async () => {
      server.use(
        http.get(`${BASE}/address-objects/ipv4`, () => {
          return HttpResponse.json({
            status: { success: true, info: [] },
            address_objects: [],
          });
        })
      );
      const objects = await client.addressObjects.list();
      expect(objects).toHaveLength(0);
    });
  });

  describe("get()", () => {
    it("returns the object for an existing name", async () => {
      const obj = await client.addressObjects.get("my-server");
      expect(obj.name).toBe("my-server");
      expect(obj.type).toBe("host");
      expect(obj.host).toBe("10.0.0.100");
      expect(obj.zone).toBe("LAN");
    });

    it("throws NotFoundError for unknown name", async () => {
      await expect(client.addressObjects.get("ghost")).rejects.toThrow(NotFoundError);
    });
  });

  describe("create()", () => {
    it("creates a new object and returns it", async () => {
      const newObj: AddressObject = {
        name: "new-host",
        type: "host",
        host: "192.168.1.50",
        zone: "LAN",
      };

      server.use(
        http.post(`${BASE}/address-objects/ipv4`, () => {
          return HttpResponse.json({ status: { success: true, info: [] } });
        }),
        http.get(`${BASE}/address-objects/ipv4/name/new-host`, () => {
          return HttpResponse.json(
            makeSingleResponse({
              address_object: {
                ipv4: { name: "new-host", zone: "LAN", host: { ip: "192.168.1.50" } },
              },
            })
          );
        })
      );

      const created = await client.addressObjects.create(newObj);
      expect(created.name).toBe("new-host");
      expect(created.host).toBe("192.168.1.50");
    });

    it("throws ConflictError when object already exists", async () => {
      server.use(
        http.post(`${BASE}/address-objects/ipv4`, () => {
          return HttpResponse.json(CONFLICT_RESPONSE);
        })
      );

      const obj: AddressObject = {
        name: "my-server",
        type: "host",
        host: "10.0.0.1",
        zone: "LAN",
      };

      await expect(client.addressObjects.create(obj)).rejects.toThrow(ConflictError);
    });
  });

  describe("update()", () => {
    it("updates an existing object", async () => {
      const updated: AddressObject = {
        name: "my-server",
        type: "host",
        host: "10.0.0.200",
        zone: "LAN",
      };

      server.use(
        http.put(`${BASE}/address-objects/ipv4/name/my-server`, () => {
          return HttpResponse.json({ status: { success: true, info: [] } });
        }),
        http.get(`${BASE}/address-objects/ipv4/name/my-server`, () => {
          return HttpResponse.json(
            makeSingleResponse({
              address_object: {
                ipv4: { name: "my-server", zone: "LAN", host: { ip: "10.0.0.200" } },
              },
            })
          );
        })
      );

      const result = await client.addressObjects.update("my-server", updated);
      expect(result.host).toBe("10.0.0.200");
    });
  });

  describe("delete()", () => {
    it("deletes an existing object without error", async () => {
      await expect(client.addressObjects.delete("my-server")).resolves.toBeUndefined();
    });

    it("throws NotFoundError for unknown name", async () => {
      server.use(
        http.delete(`${BASE}/address-objects/ipv4/name/ghost`, () => {
          return HttpResponse.json(NOT_FOUND_RESPONSE);
        })
      );

      await expect(client.addressObjects.delete("ghost")).rejects.toThrow(NotFoundError);
    });
  });

  describe("ensure()", () => {
    it("creates object and returns [obj, true] when not found", async () => {
      let getCallCount = 0;

      server.use(
        http.get(`${BASE}/address-objects/ipv4/name/brand-new`, () => {
          getCallCount++;
          if (getCallCount === 1) {
            return HttpResponse.json(NOT_FOUND_RESPONSE);
          }
          return HttpResponse.json(
            makeSingleResponse({
              address_object: {
                ipv4: { name: "brand-new", zone: "DMZ", host: { ip: "172.16.0.1" } },
              },
            })
          );
        }),
        http.post(`${BASE}/address-objects/ipv4`, () => {
          return HttpResponse.json({ status: { success: true, info: [] } });
        })
      );

      const newObj: AddressObject = {
        name: "brand-new",
        type: "host",
        host: "172.16.0.1",
        zone: "DMZ",
      };

      const [result, wasCreated] = await client.addressObjects.ensure(newObj);
      expect(wasCreated).toBe(true);
      expect(result.name).toBe("brand-new");
    });

    it("updates object and returns [obj, false] when it exists", async () => {
      let getCallCount = 0;

      server.use(
        http.get(`${BASE}/address-objects/ipv4/name/my-server`, () => {
          getCallCount++;
          if (getCallCount === 1) {
            return HttpResponse.json(makeSingleResponse(ADDR_OBJ_HOST));
          }
          return HttpResponse.json(
            makeSingleResponse({
              address_object: {
                ipv4: { name: "my-server", zone: "LAN", host: { ip: "10.0.0.200" } },
              },
            })
          );
        }),
        http.put(`${BASE}/address-objects/ipv4/name/my-server`, () => {
          return HttpResponse.json({ status: { success: true, info: [] } });
        })
      );

      const obj: AddressObject = {
        name: "my-server",
        type: "host",
        host: "10.0.0.200",
        zone: "LAN",
      };

      const [result, wasCreated] = await client.addressObjects.ensure(obj);
      expect(wasCreated).toBe(false);
      expect(result.host).toBe("10.0.0.200");
    });
  });

  describe("transaction()", () => {
    it("commits on success", async () => {
      let commitCalled = false;

      server.use(
        http.post(`${BASE}/config/pending`, () => {
          commitCalled = true;
          return HttpResponse.json({ status: { success: true, info: [] } });
        })
      );

      await client.transaction(async () => {
        // no-op
      });

      expect(commitCalled).toBe(true);
    });

    it("rolls back on exception", async () => {
      let rollbackCalled = false;

      server.use(
        http.delete(`${BASE}/config/pending`, () => {
          rollbackCalled = true;
          return HttpResponse.json({ status: { success: true, info: [] } });
        })
      );

      await expect(
        client.transaction(async () => {
          throw new Error("Simulated failure");
        })
      ).rejects.toThrow("Simulated failure");

      expect(rollbackCalled).toBe(true);
    });
  });
});
