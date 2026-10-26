import { createRequire } from 'node:module';

// The verifier stages this suite under the restored workspace. Product code is loaded through
// require at the moment a case runs, so a broken submission fails cases rather than collection.
const load = createRequire(import.meta.url);

/** The library as users import it: the package's declared entry. */
export function pkg(): any {
  return load('/workspace');
}

/** The library source the package is built from, compiled by the verifier. */
export function src(): any {
  return load('/workspace/.htests/srcbuild/utils.js');
}

/** Port of the local HTTP service the verifier starts for the request-following cases. */
export const PORT: string = process.env.TEST_PORT || '18080';

/** URL of the local service, addressed by a reserved name. */
export function url(host: string, path = '/final'): string {
  return `http://${host}:${PORT}${path}`;
}

/** URL of the local service whose authority carries the given credentials. */
export function credUrl(userinfo: string, host: string, path = '/final'): string {
  return `http://${userinfo}@${host}:${PORT}${path}`;
}
