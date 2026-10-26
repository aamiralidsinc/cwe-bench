# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `ultrajson-s2`. Pattern: `A+B`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: ["GHSA-3J69-69WJ-XQX2", "CVE-2026-54911", "PYSEC-2026-2294"]; ultrajson/ultrajson; CWE-20 improper input validation: UTF-8 sequence validation / silent Unicode rewriting in the JSON string encoder (with a memory-safety edge from the undersized end-of-buffer checks)
- Pinned (vulnerable) commit: d18f6bdfd53a40a572dddced99df296a6ad17009. Published fix: 169eaf36b1116fece5034ee79a7a0ef3f6deedcf.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "480",
 "advisory_ids": [
  "GHSA-3J69-69WJ-XQX2",
  "CVE-2026-54911",
  "PYSEC-2026-2294"
 ],
 "repo": "ultrajson/ultrajson",
 "pinned_commit": "d18f6bdfd53a40a572dddced99df296a6ad17009",
 "fix_commits": [
  "169eaf36b1116fece5034ee79a7a0ef3f6deedcf"
 ],
 "trust_decision": {
  "summary": "Bytes are trusted input whenever ujson.dumps/encode/dump runs with reject_bytes=False; the decision to emit a byte sequence verbatim or to fold it into a \\uXXXX escape is made in Buffer_EscapeStringValidated, which must therefore reject malformed, truncated or out-of-range UTF-8 instead of silently rewriting it (encoder side only; reached only when forceASCII is on).",
  "evidence": [
   "src/ujson/python/objToJSON.c:426-438",
   "src/ujson/python/objToJSON.c:705",
   "src/ujson/python/objToJSON.c:906-923",
   "src/ujson/lib/ultrajsonenc.c:350-443",
   "src/ujson/python/objToJSON.c:867"
  ]
 },
 "landing_point": {
  "where": "src/ujson/python/objToJSON.c:426-438",
  "why": "The summary's repro is ujson.dumps(bytes, reject_bytes=False); this branch is the only place a bytes object becomes JT_UTF8, so a reader who greps reject_bytes or the bytes path lands here, and the trail then continues into the C encoder."
 },
 "fix_sites": [
  {
   "where": "src/ujson/lib/ultrajsonenc.c:350-380",
   "entry_point": "ujson.dumps / ujson.encode (values via objToJSON.c:906-923, dict keys via objToJSON.c:690-703)",
   "module_kind": "C encoder library (src/ujson/lib)"
  },
  {
   "where": "src/ujson/lib/ultrajsonenc.c:382-416",
   "entry_point": "ujson.dumps / ujson.encode (values via objToJSON.c:906-923, dict keys via objToJSON.c:690-703)",
   "module_kind": "C encoder library (src/ujson/lib)"
  },
  {
   "where": "src/ujson/lib/ultrajsonenc.c:417-443",
   "entry_point": "ujson.dumps / ujson.encode (values via objToJSON.c:906-923, dict keys via objToJSON.c:690-703)",
   "module_kind": "C encoder library (src/ujson/lib)"
  },
  {
   "where": "src/ujson/lib/ultrajsondec.c:534",
   "entry_point": "ujson.loads / ujson.decode (JSONtoObj.c:249, via ujson.load at ujson.c:69)",
   "module_kind": "C decoder library (src/ujson/lib), error-text only"
  },
  {
   "where": "src/ujson/lib/ultrajsondec.c:557",
   "entry_point": "ujson.loads / ujson.decode (JSONtoObj.c:249, via ujson.load at ujson.c:69)",
   "module_kind": "C decoder library (src/ujson/lib), error-text only"
  },
  {
   "where": "src/ujson/lib/ultrajsondec.c:580",
   "entry_point": "ujson.loads / ujson.decode (JSONtoObj.c:249, via ujson.load at ujson.c:69)",
   "module_kind": "C decoder library (src/ujson/lib), error-text only"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/ujson/lib/ultrajsondec.c:519-584"
 },
 "O3_reason_to_dismiss": "The advisory and its repro are about ujson.dumps(), and the published fix only relabelled three decoder error strings, so the decoder's own UTF-8 validator (ujson.loads/decode/load) can be argued to be a separate feature this advisory never covered.",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "UTF-8-encoded lone surrogates must keep being accepted and rewritten to \\udXXX: ujson.dumps({b\"\\xed\\xa0\\x80\": b\"\\xed\\xbf\\xbf\"}, reject_bytes=False) must still produce '{\"\\ud800\":\"\\udfff\"}'.  The fix deliberately leaves the surrogate check commented out (fix.diff:93-100), so an over-broad strict-UTF-8 fix that rejects lead 0xed with second byte >= 0xa0 breaks this pinned test.",
  "where": "tests/test_ujson.py:648-650"
 },
 "O6_input_shapes": [
  "bytes as a dumps() value, as a dict key (bytes keys never reach the reject_bytes check, objToJSON.c:220-224), and nested in lists/dicts",
  "2-, 3- and 4-byte lead bytes (0xc0-0xf7) with well-formed continuations",
  "truncated sequences: a lead byte followed by 0, 1 or 2 bytes (the old end-io bounds at ultrajsonenc.c:355, 388, 421 were each one byte short)",
  "invalid continuation bytes: any following byte whose top bits are not 0b10",
  "overlong 2-, 3- and 4-byte encodings (decoded value < 0x80 / 0x800 / 0x10000)",
  "4-byte sequences above U+10FFFF (0xf4 0x90.. and 0xf5-0xf7)",
  "5- and 6-byte lead bytes 0xf8-0xfd ('Unsupported UTF-8 sequence length')",
  "lone continuation bytes 0x80-0xbf and 0xfe/0xff, which the C validator passes through and the final PyUnicode_DecodeUTF8 rejects (objToJSON.c:867)",
  "variants of the same call: sort_keys, indent, dump() to a file object, ensure_ascii=True (validated path) vs False (unvalidated path)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "src/ujson/python/objToJSON.c:109-145",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "decode_string accepts any byte with the high bit set as a continuation byte ((oct & 0x80) != 0x80), so ujson.loads(b'\"\\xc3\\xc3\"') silently yields U+00C3 instead of raising - the exact bug class the encoder fix closes",
   "where": "src/ujson/lib/ultrajsondec.c:529, 549, 572",
   "reason_to_dismiss": "The advisory names ujson.dumps() only; the decoder is the opposite direction and the published fix touched it purely for error wording, so loads() is a different feature.",
   "distance": "another function in the other C library file (src/ujson/lib/ultrajsondec.c), reached through a different public API (ujson.loads/decode/load)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "lone continuation bytes 0x80-0xbf inside a JSON string are copied straight into the result as U+0080-U+00BF, so ujson.loads(b'\"\\x9b\"') returns '\\x9b' where b'\\x9b'.decode('utf-8') raises",
   "where": "src/ujson/lib/ultrajsondec.c:519-523",
   "reason_to_dismiss": "Same as above: the report and the fix are about dumping bytes; a one-byte string body can be dismissed as a bare bytes-decoding concern rather than a UTF-8 sequence bug.",
   "distance": "same decoder file as the previous route, one switch arm above the length cases",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "decode_string's 4-byte arm has no >U+10FFFF check, so b'\"\\xf4\\x90\\x80\\x80\"' is accepted and the codepoint 0x110000 is handed to PyUnicode_FromKindAndData",
   "where": "src/ujson/lib/ultrajsondec.c:562-583",
   "reason_to_dismiss": "The encoder's >U+10FFFF guard is new in this fix and clearly encoder-specific; a solver can argue the decoder was never in the advisory's scope and simply was not changed there.",
   "distance": "same decoder function, third length arm",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "the exported C API JSON_EncodeObject with enc->forceASCII == 0 writes the source bytes through Buffer_EscapeStringUnvalidated with no validation at all, and there is no final PyUnicode_DecodeUTF8 backstop at this layer",
   "where": "src/ujson/lib/ultrajsonenc.c:917-923 (caller-visible entry: ultrajson.h:324, JSON_EncodeObject at ultrajsonenc.c:955)",
   "reason_to_dismiss": "forceASCII=0 is a caller-chosen 'raw UTF-8 passthrough' mode of the embeddable C library (src/ujson/lib/Makefile builds libujson.a); the advisory is about the Python ujson.dumps() surface, so the C API looks unsupported/out of scope.",
   "distance": "same file but a different API layer (C library entry vs Python binding), reachable only by embedding libujson.a",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/ujson/lib/ultrajsondec.c:519-523",
   "sibling": "a strict-UTF-8 arm in decode_string that rejects lone continuation bytes instead of mapping them to U+0080-U+00BF",
   "why_realistic": "the file already contains a hand-written per-length UTF-8 validator with overlong checks; a maintainer fixing the same class of bug would naturally add the missing arm here rather than rewrite the loop."
  },
  {
   "where": "src/ujson/python/objToJSON.c:214-242",
   "sibling": "UTF-8 / reject_bytes validation for bytes dict keys in Dict_convertKey",
   "why_realistic": "keys take a different conversion route than values and bytes keys are exempt from reject_bytes (objToJSON.c:220-224), so a fix author who read the report as 'bytes in dumps' could plausibly add a key-side check."
  },
  {
   "where": "src/ujson/lib/ultrajsonenc.c:917-923",
   "sibling": "a validated variant of Buffer_EscapeStringUnvalidated used when ensure_ascii=False",
   "why_realistic": "the unvalidated escaping path sits directly next to the validated one and is selected by a single flag, so a maintainer could mirror the checks there to make the two paths symmetric."
  }
 ],
 "O9_family": "CWE-20 improper input validation: UTF-8 sequence validation / silent Unicode rewriting in the JSON string encoder (with a memory-safety edge from the undersized end-of-buffer checks)",
 "O9_dos": false,
 "O10_build": {
  "language": "C extension for CPython, with vendored C++ (double-conversion)",
  "toolchain": "CPython >= 3.10, setuptools>=77 + setuptools-scm (pyproject.toml:1-5), C and C++ compiler, -lstdc++ -lm (setup.py:42-56); single extension module 'ujson'",
  "services": [],
  "offline_after_build": true,
  "project_tests": "pytest tests/test_ujson.py - reject_bytes tests (tests/test_ujson.py:1202-1229), surrogate round-trip via bytes (tests/test_ujson.py:643-654), UTF-8 boundary decode (tests/test_ujson.py:1158-1168); tests/fuzz.py is an Atheris harness"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/ujson/lib/ultrajsonenc.c, src/ujson/lib/ultrajsondec.c (message labels only)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add the missing continuation-byte test to the 2-byte arm only (the shape from the report), confirm with one b'\\xcf\\x13' example, and stop."
 },
 "out_of_scope_notes": [
  "ensure_ascii=False routes through Buffer_EscapeStringUnvalidated (src/ujson/lib/ultrajsonenc.c:191-300), which performs no UTF-8 validation but whose output is still rejected by PyUnicode_DecodeUTF8 at src/ujson/python/objToJSON.c:867, so it is not scored as an O8 hole; that path does, however, contain its own unchecked end-of-buffer read at src/ujson/lib/ultrajsonenc.c:204 and 296 - noted, not pursued."
 ],
 "unverified": [
  "Repository size in MB could not be measured in this session (no shell available), so tiny_repo could be neither confirmed nor ruled out; the tree has 107 files, most of the bulk being the vendored double-conversion sources and its test tables.",
  "Whether CPython's PyUnicode_FromKindAndData (src/ujson/python/JSONtoObj.c:84) rejects a codepoint above U+10FFFF at object creation, so the end-to-end result of ujson.loads(b'\"\\xf4\\x90\\x80\\x80\"') is not verified; only the decoder's missing range check is.",
  "Whether the hidden behavioural tests assert the exact hyphenated encoder messages ('Overlong 2-byte ...', 'Invalid continuation byte in 3-byte ...'), which would make the wording-only hunks graded rather than incidental.",
  "The full advisory text was not available beyond the summary line, so the question of whether the advisory's property is meant to cover ujson.loads() is judged from the summary and the diff alone."
 ]
}
  ```
- Published fix sites:   - src/ujson/lib/ultrajsonenc.c:350-380 — entry point: ujson.dumps / ujson.encode (values via objToJSON.c:906-923, dict keys via objToJSON.c:690-703) [C encoder library (src/ujson/lib)]
  - src/ujson/lib/ultrajsonenc.c:382-416 — entry point: ujson.dumps / ujson.encode (values via objToJSON.c:906-923, dict keys via objToJSON.c:690-703) [C encoder library (src/ujson/lib)]
  - src/ujson/lib/ultrajsonenc.c:417-443 — entry point: ujson.dumps / ujson.encode (values via objToJSON.c:906-923, dict keys via objToJSON.c:690-703) [C encoder library (src/ujson/lib)]
  - src/ujson/lib/ultrajsondec.c:534 — entry point: ujson.loads / ujson.decode (JSONtoObj.c:249, via ujson.load at ujson.c:69) [C decoder library (src/ujson/lib), error-text only]
  - src/ujson/lib/ultrajsondec.c:557 — entry point: ujson.loads / ujson.decode (JSONtoObj.c:249, via ujson.load at ujson.c:69) [C decoder library (src/ujson/lib), error-text only]
  - src/ujson/lib/ultrajsondec.c:580 — entry point: ujson.loads / ujson.decode (JSONtoObj.c:249, via ujson.load at ujson.c:69) [C decoder library (src/ujson/lib), error-text only]
- Uncovered routes to confirm (pattern B):   - src/ujson/lib/ultrajsondec.c:529, 549, 572 — decode_string accepts any byte with the high bit set as a continuation byte ((oct & 0x80) != 0x80), so ujson.loads(b'"\xc3\xc3"') silently yields U+00C3 instead of raising - the exact bug class the encoder fix closes (reason to dismiss: The advisory names ujson.dumps() only; the decoder is the opposite direction and the published fix touched it purely for error wording, so loads() is a different feature.; still in latest: unknown)
  - src/ujson/lib/ultrajsondec.c:519-523 — lone continuation bytes 0x80-0xbf inside a JSON string are copied straight into the result as U+0080-U+00BF, so ujson.loads(b'"\x9b"') returns '\x9b' where b'\x9b'.decode('utf-8') raises (reason to dismiss: Same as above: the report and the fix are about dumping bytes; a one-byte string body can be dismissed as a bare bytes-decoding concern rather than a UTF-8 sequence bug.; still in latest: unknown)
  - src/ujson/lib/ultrajsondec.c:562-583 — decode_string's 4-byte arm has no >U+10FFFF check, so b'"\xf4\x90\x80\x80"' is accepted and the codepoint 0x110000 is handed to PyUnicode_FromKindAndData (reason to dismiss: The encoder's >U+10FFFF guard is new in this fix and clearly encoder-specific; a solver can argue the decoder was never in the advisory's scope and simply was not changed there.; still in latest: unknown)
  - src/ujson/lib/ultrajsonenc.c:917-923 (caller-visible entry: ultrajson.h:324, JSON_EncodeObject at ultrajsonenc.c:955) — the exported C API JSON_EncodeObject with enc->forceASCII == 0 writes the source bytes through Buffer_EscapeStringUnvalidated with no validation at all, and there is no final PyUnicode_DecodeUTF8 backstop at this layer (reason to dismiss: forceASCII=0 is a caller-chosen 'raw UTF-8 passthrough' mode of the embeddable C library (src/ujson/lib/Makefile builds libujson.a); the advisory is about the Python ujson.dumps() surface, so the C API looks unsupported/out of scope.; still in latest: unknown)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/ultrajson-s2/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/ultrajson-s2/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/ultrajson-s2/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/ultrajson-s2/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/ultrajson-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/ultrajson-s2/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/ultrajson-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py ultrajson-s2 --only static
python3 -I common/gate/gate.py ultrajson-s2 --only nop
python3 -I common/gate/gate.py ultrajson-s2 --only oracle
python3 -I common/gate/gate.py ultrajson-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/ultrajson-s2/`;
  - edit only `tasks/ultrajson-s2/`, `build/ultrajson-s2/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
