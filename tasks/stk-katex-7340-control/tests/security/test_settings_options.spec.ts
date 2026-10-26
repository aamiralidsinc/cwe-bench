import katex from "katex";
import {ATTACK_URL, carriesUrlAsAttribute, cleanPrototype, PLANTED_EXPANSION} from "../support/proto";

afterEach(cleanPrototype);

describe("render options only come from the caller's own entries", () => {
    it("ignores a trust entry inherited from the shared prototype", () => {
        (Object.prototype as Record<string, unknown>).trust = true;
        const out = katex.renderToString(`\\href{${ATTACK_URL}}{x}`);
        expect(carriesUrlAsAttribute(out, ATTACK_URL)).toBe(false);
    });

    it("ignores a trust entry inherited from the options object's prototype", () => {
        const options = Object.create({trust: true});
        const out = katex.renderToString(`\\href{${ATTACK_URL}}{x}`, options);
        expect(carriesUrlAsAttribute(out, ATTACK_URL)).toBe(false);
    });

    it("ignores an inherited trust entry for a bare URL command", () => {
        (Object.prototype as Record<string, unknown>).trust = true;
        const out = katex.renderToString(`\\url{${ATTACK_URL}}`);
        expect(carriesUrlAsAttribute(out, ATTACK_URL)).toBe(false);
    });

    it("ignores an inherited trust entry for an image command", () => {
        (Object.prototype as Record<string, unknown>).trust = true;
        const out = katex.renderToString(`\\includegraphics{${ATTACK_URL}}`);
        expect(carriesUrlAsAttribute(out, ATTACK_URL)).toBe(false);
    });

    it("ignores a macro table inherited from the options object's prototype", () => {
        (Object.prototype as Record<string, unknown>).macros = {"\\pwn": PLANTED_EXPANSION};
        let out = "";
        try {
            out = katex.renderToString("\\pwn");
        } catch (e) {
            // an unknown control sequence is a valid refusal
        }
        expect(out).not.toContain("PWNED");
    });
});
