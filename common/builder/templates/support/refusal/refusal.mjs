// Refusal-tolerant assertions for JS/TS security tests (vitest, jest, node:test). Copy into tests/support/.
//
// A security test that drives a hardened entry point must accept every secure outcome the instruction allows:
// the call is refused (a client error, or one of the product's own refusal errors), or it completes and leaves
// nothing unsafe behind. A crash is not a refusal: a 5xx, or an error outside the declared refusal types, fails
// the test, so a fix that merely breaks the call is still caught (wrong-fix class crash_as_refusal).
//
//   import { refusedOr } from '../support/refusal.mjs';
//   await refusedOr(() => client.fetch(url), {
//     ok: (res) => expect(res.body).not.toContain(SECRET),
//     refusals: [ForbiddenError, (e) => e.code === 'ERR_BLOCKED_DESTINATION'],
//   });
//   expect(network.reached('internal')).toBe(0);   // side effects are checked after every outcome

const STATUS_KEYS = ['status', 'statusCode', 'code'];

function statusOf(obj) {
  if (obj == null || typeof obj !== 'object') return null;
  for (const k of STATUS_KEYS) {
    const v = obj[k];
    if (Number.isInteger(v) && v >= 100 && v <= 599) return v;
  }
  if (obj.response && obj.response !== obj) return statusOf(obj.response);
  return null;
}

function matches(err, refusals) {
  return refusals.some((r) => {
    if (typeof r !== 'function') return false;
    if (r.prototype instanceof Error || r === Error) return err instanceof r;
    try { return Boolean(r(err)); } catch { return false; }
  });
}

export async function attempt(call, { refusals = [] } = {}) {
  let value;
  try {
    value = await call();
  } catch (err) {
    if (err && err.name === 'AssertionError') throw err;
    const status = statusOf(err);
    if (status !== null) {
      if (status >= 400 && status < 500) return { refused: true, reason: `${err?.name ?? 'error'} ${status}` };
      throw err;
    }
    if (matches(err, refusals)) return { refused: true, reason: err?.name ?? String(err) };
    throw err;
  }
  const status = statusOf(value);
  if (status !== null && status >= 400 && status < 500) return { refused: true, value, reason: `status ${status}` };
  if (status !== null && status >= 500) throw new Error(`server error ${status}: a crash is not a refusal`);
  return { refused: false, value };
}

export async function refusedOr(call, { ok, refusals = [] } = {}) {
  const out = await attempt(call, { refusals });
  if (!out.refused && ok) {
    const r = await ok(out.value);
    if (r === false) throw new Error('the call completed and its result is unsafe');
  }
  return out;
}

export async function mustRefuse(call, { refusals = [] } = {}) {
  const out = await attempt(call, { refusals });
  if (!out.refused) throw new Error('expected a refusal (a client error or a refusal error), the call completed');
  return out;
}
