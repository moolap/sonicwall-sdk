/**
 * Shared response normalization (firmware envelope variants).
 */

export function normalizeGetFromPlural(
  response: Record<string, unknown>,
  options: {
    pluralKey: string;
    singularKey: string;
    predicate?: (item: Record<string, unknown>) => boolean;
  }
): Record<string, unknown> {
  const { pluralKey, singularKey, predicate } = options;
  const items = response[pluralKey];
  if (!Array.isArray(items) || items.length === 0) {
    return response;
  }

  let selected: Record<string, unknown> | null = null;
  if (predicate) {
    for (const item of items) {
      if (item && typeof item === "object" && predicate(item as Record<string, unknown>)) {
        selected = item as Record<string, unknown>;
        break;
      }
    }
  }
  if (selected === null) {
    const first = items[0];
    if (first && typeof first === "object") {
      selected = first as Record<string, unknown>;
    }
  }
  if (selected === null) {
    return response;
  }

  const inner = selected[singularKey];
  if (singularKey in selected && typeof inner === "object" && inner !== null) {
    return { [singularKey]: inner };
  }
  return { [singularKey]: selected };
}

export function unwrapIpv4(
  item: Record<string, unknown>,
  wrappedKey: string
): Record<string, unknown> | null {
  if (wrappedKey in item && typeof item[wrappedKey] === "object" && item[wrappedKey] !== null) {
    const inner = item[wrappedKey] as Record<string, unknown>;
    const ipv4 = inner["ipv4"];
    if (typeof ipv4 === "object" && ipv4 !== null) {
      return ipv4 as Record<string, unknown>;
    }
    return inner;
  }
  const ipv4 = item["ipv4"];
  if (typeof ipv4 === "object" && ipv4 !== null) {
    return ipv4 as Record<string, unknown>;
  }
  return null;
}
