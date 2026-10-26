import { getNodeParameters } from 'n8n-workflow';

/**
 * Models how n8n turns stored parameter values into what a node reads at run time.
 *
 * Two documented steps matter here:
 *  - at load time, n8n fills defaults and, for a property that declares that it takes no data
 *    expression, removes the leading "=" from a value written as an expression, so that the
 *    expression engine never evaluates it;
 *  - at run time, a value that still starts with "=" is evaluated against the current item.
 *
 * The load-time step is the real n8n-workflow function, not a re-implementation.
 */
export type JsonObject = Record<string, unknown>;

export interface ExpressionContext {
  env?: Record<string, string>;
  vars?: Record<string, string>;
}

export interface NodeContextOptions extends ExpressionContext {
  credentials?: JsonObject;
}

// A deliberately small model of the expression forms this project's users write. It evaluates
// only a value that starts with "=" and understands the item, environment and variable scopes.
function readExpression(expression: string, item: JsonObject | undefined, ctx: ExpressionContext): unknown {
  const expr = expression.trim();

  let match = /^\$json(?:\.([A-Za-z0-9_]+))?$/.exec(expr);
  if (match) {
    if (item === undefined) throw new Error('No item data available to resolve $json');
    return match[1] === undefined ? item : item[match[1]];
  }

  match = /^\$json\[['"]([^'"]+)['"]\]$/.exec(expr);
  if (match) {
    if (item === undefined) throw new Error('No item data available to resolve $json');
    return item[match[1]];
  }

  match = /^\$env\.([A-Za-z0-9_]+)$/.exec(expr);
  if (match) return (ctx.env ?? {})[match[1]];

  match = /^\$vars\.([A-Za-z0-9_]+)$/.exec(expr);
  if (match) return (ctx.vars ?? {})[match[1]];

  throw new Error(`Unsupported expression in this harness: ${expr}`);
}

function interpolate(text: string, item: JsonObject | undefined, ctx: ExpressionContext): unknown {
  const whole = /^\{\{([\s\S]*)\}\}$/.exec(text.trim());
  if (whole) return readExpression(whole[1], item, ctx);

  return text.replace(/\{\{([\s\S]*?)\}\}/g, (_all, inner: string) =>
    String(readExpression(inner, item, ctx)),
  );
}

/** Evaluates a stored value the way n8n does at run time. */
export function resolveValue(
  value: unknown,
  item: JsonObject | undefined,
  ctx: ExpressionContext = {},
): unknown {
  if (typeof value === 'string') {
    return value.startsWith('=') ? interpolate(value.slice(1), item, ctx) : value;
  }
  if (Array.isArray(value)) return value.map((entry) => resolveValue(entry, item, ctx));
  if (value && typeof value === 'object') {
    const out: JsonObject = {};
    for (const [key, entry] of Object.entries(value as JsonObject)) {
      out[key] = resolveValue(entry, item, ctx);
    }
    return out;
  }
  return value;
}

/** Applies n8n's load-time parameter handling (defaults plus the expression prefix rule). */
export function loadNodeParameters(properties: unknown, raw: JsonObject): JsonObject {
  return getNodeParameters(
    properties as Parameters<typeof getNodeParameters>[0],
    raw as Parameters<typeof getNodeParameters>[1],
    true,
    false,
    null,
    null,
  ) as JsonObject;
}

/**
 * A mock execution/load-options context backed by values that went through loadNodeParameters.
 * `rawExpressions` is honoured, so a product fix that inspects the stored value directly works.
 */
export function makeContext(
  loaded: JsonObject,
  items: JsonObject[],
  options: NodeContextOptions = {},
) {
  const ctx: ExpressionContext = { env: options.env, vars: options.vars };

  return {
    getInputData: () => items.map((json) => ({ json })),
    getNodeParameter: (
      name: string,
      itemIndex: number,
      fallback?: unknown,
      parameterOptions?: { rawExpressions?: boolean },
    ): unknown => {
      const stored = name in loaded ? loaded[name] : fallback;
      if (parameterOptions?.rawExpressions) return stored;
      return resolveValue(stored, items[itemIndex] ?? items[0], ctx);
    },
    getNode: () => ({
      name: 'SQLite',
      id: '1',
      type: 'sqliteNode',
      typeVersion: 1,
      position: [0, 0],
    }),
    continueOnFail: () => false,
    getCredentials: async (): Promise<JsonObject> => options.credentials ?? {},
  };
}

/**
 * Models how n8n resolves the values stored in a credential. Credential expressions have no
 * item data, so only the environment and variable scopes are available.
 */
export function resolveCredentialData(
  properties: unknown,
  raw: JsonObject,
  ctx: ExpressionContext = {},
): JsonObject {
  const loaded = loadNodeParameters(properties, raw);
  const resolved: JsonObject = {};
  for (const [key, entry] of Object.entries(loaded)) {
    resolved[key] = resolveValue(entry, undefined, ctx);
  }
  return resolved;
}
