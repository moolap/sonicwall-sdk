/**
 * MSW request handlers for SonicWall API mocking.
 */

import { http, HttpResponse } from "msw";

export const BASE = "https://192.168.1.1/api/sonicos";

const AUTH_SUCCESS = {
  status: { success: true, info: [{ level: "info", code: 200, message: "Success" }] },
};

const COMMIT_SUCCESS = {
  status: {
    success: true,
    info: [{ level: "info", code: 200, message: "Changes committed." }],
  },
};

export const ADDR_OBJ_HOST = {
  address_object: {
    ipv4: { name: "my-server", zone: "LAN", host: { ip: "10.0.0.100" } },
  },
};

export const ADDR_OBJ_NETWORK = {
  address_object: {
    ipv4: {
      name: "internal-net",
      zone: "LAN",
      network: { subnet: "10.0.0.0", mask: "255.255.255.0" },
    },
  },
};

const SESSION_COOKIE = "test-session-cookie";

export function makeListResponse(
  ...objects: Array<typeof ADDR_OBJ_HOST>
): Record<string, unknown> {
  return {
    status: { success: true, info: [] },
    address_objects: objects,
  };
}

export function makeSingleResponse(
  obj: Record<string, unknown>
): Record<string, unknown> {
  return {
    status: { success: true, info: [] },
    ...obj,
  };
}

export const NOT_FOUND_RESPONSE = {
  status: {
    success: false,
    info: [{ level: "error", code: 1030, message: "Object not found" }],
  },
};

export const CONFLICT_RESPONSE = {
  status: {
    success: false,
    info: [{ level: "error", code: 1055, message: "Object already exists" }],
  },
};

export const handlers = [
  // Auth
  http.post(`${BASE}/auth`, () => {
    return new HttpResponse(JSON.stringify(AUTH_SUCCESS), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Set-Cookie": `smngsess=${SESSION_COOKIE}; Path=/; Secure; HttpOnly`,
      },
    });
  }),

  http.delete(`${BASE}/auth`, () => {
    return HttpResponse.json(AUTH_SUCCESS);
  }),

  // Commit / Rollback
  http.post(`${BASE}/config/pending`, () => {
    return HttpResponse.json(COMMIT_SUCCESS);
  }),

  http.delete(`${BASE}/config/pending`, () => {
    return HttpResponse.json(COMMIT_SUCCESS);
  }),

  // Address objects list
  http.get(`${BASE}/address-objects/ipv4`, () => {
    return HttpResponse.json(makeListResponse(ADDR_OBJ_HOST, ADDR_OBJ_NETWORK));
  }),

  // Address object get by name
  http.get(`${BASE}/address-objects/ipv4/name/:name`, ({ params }) => {
    const name = params["name"];
    if (name === "my-server") {
      return HttpResponse.json(makeSingleResponse(ADDR_OBJ_HOST));
    }
    return HttpResponse.json(NOT_FOUND_RESPONSE);
  }),

  // Address object create
  http.post(`${BASE}/address-objects/ipv4`, () => {
    return HttpResponse.json(AUTH_SUCCESS);
  }),

  // Address object update
  http.put(`${BASE}/address-objects/ipv4/name/:name`, () => {
    return HttpResponse.json(AUTH_SUCCESS);
  }),

  // Address object delete
  http.delete(`${BASE}/address-objects/ipv4/name/:name`, ({ params }) => {
    const name = params["name"];
    if (name === "my-server") {
      return HttpResponse.json(AUTH_SUCCESS);
    }
    return HttpResponse.json(NOT_FOUND_RESPONSE);
  }),
];
