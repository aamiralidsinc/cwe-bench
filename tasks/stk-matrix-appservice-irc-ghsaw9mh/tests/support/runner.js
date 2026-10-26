#!/usr/bin/env node
"use strict";

/*
 * Hidden-suite runner. Usage: node runner.js <security|functional> <output.xml>
 *
 * Loads the project's own Jasmine installation, runs the group's spec files through the real
 * AppService dispatch and its mock Matrix/IRC peers, and writes one JUnit XML file.
 */

const fs = require("fs");
const path = require("path");

const GROUP = process.argv[2];
const OUT = process.argv[3];
const WS = process.env.PRODUCT_ROOT || "/workspace";

function esc(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&apos;");
}

function writeXml(results) {
    const failures = results.filter((r) => r.status !== "passed").length;
    // The project's own specs reuse a few descriptions; the scorer keys on classname::name.
    const seen = new Map();
    for (const r of results) {
        const base = r.fullName || r.name || "unnamed";
        const count = (seen.get(base) || 0) + 1;
        seen.set(base, count);
        r.uniqueName = count === 1 ? base : `${base} #${count}`;
    }
    const lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        `<testsuite name="${esc(GROUP)}" tests="${results.length}" failures="${failures}" errors="0" skipped="0">`,
    ];
    for (const r of results) {
        const name = r.uniqueName;
        if (r.status === "passed") {
            lines.push(`  <testcase classname="${esc(GROUP)}" name="${esc(name)}"/>`);
        }
        else {
            const message = (r.messages && r.messages.length ? r.messages.join("\n") : r.status) || "failed";
            lines.push(`  <testcase classname="${esc(GROUP)}" name="${esc(name)}">`);
            lines.push(`    <failure message="${esc(message).slice(0, 800)}">${esc(message).slice(0, 8000)}</failure>`);
            lines.push("  </testcase>");
        }
    }
    lines.push("</testsuite>", "");
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, lines.join("\n"));
}

async function main() {
    const results = [];
    let runner;
    try {
        const Jasmine = require(path.join(WS, "node_modules", "jasmine"));
        runner = new Jasmine({ projectBaseDir: WS });
        const specs = GROUP === "security" ? [
            path.join(WS, ".htests", "security", "reply_entitlement.spec.js"),
        ] : [
            path.join(WS, ".htests", "functional", "relay_keeps_working.spec.js"),
            path.join(WS, "spec", "unit", "MessageDiff.spec.js"),
            path.join(WS, "spec", "unit", "TrimString.spec.js"),
            path.join(WS, "spec", "integ", "matrix-to-irc.spec.js"),
        ];
        for (const spec of specs) {
            if (!fs.existsSync(spec)) {
                throw new Error(`missing spec file: ${spec}`);
            }
        }
        runner.exitOnCompletion = false;
        runner.loadConfig({
            spec_dir: WS,
            spec_files: specs,
            helpers: [],
            random: false,
            stopSpecOnExpectationFailure: false,
        });
        runner.jasmine.DEFAULT_TIMEOUT_INTERVAL = 30000;
        runner.addReporter({
            specDone: (result) => {
                results.push({
                    status: result.status,
                    fullName: result.fullName,
                    messages: (result.failedExpectations || []).map((f) => f.message),
                });
            },
        });
        await runner.execute();
    }
    catch (err) {
        results.push({
            status: "failed",
            fullName: `harness: ${GROUP} suite`,
            messages: [String(err && (err.stack || err.message) || err)],
        });
    }
    writeXml(results);
    const failed = results.some((r) => r.status !== "passed");
    process.exit(failed ? 1 : 0);
}

main();
