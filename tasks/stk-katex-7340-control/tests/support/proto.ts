/* Shared cleanup for the prototype-pollution security cases.
 * Every case plants one entry on the shared object prototype and removes it
 * afterwards, so no case can influence another one in the same worker.
 */
export const POLLUTED_KEYS = [
    "trust",
    "default",
    "processor",
    "protocol",
    "url",
    "macros",
    "delimiters",
    "ignoredTags",
    "ignoredClasses",
    "errorCallback",
    "\\pwn",
    "\\href",
];

export function cleanPrototype(): void {
    for (const key of POLLUTED_KEYS) {
        delete (Object.prototype as Record<string, unknown>)[key];
    }
}

export const ATTACK_URL = "javascript:alert(1)";

/** Macro expansion that renders as one contiguous word, so a marker check can see it. */
export const PLANTED_EXPANSION = "\\text{PWNED}";

/** True when the markup carries `url` as the value of an href/src attribute. */
export function carriesUrlAsAttribute(markup: string, url: string): boolean {
    const escaped = url.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp('(?:href|src)\\s*=\\s*"' + escaped + '"', "i").test(markup);
}
