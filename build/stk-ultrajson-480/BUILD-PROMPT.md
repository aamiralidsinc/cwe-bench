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

Project root: `/home/mara/cwe-bench`. Task: `stk-ultrajson-480`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 480; CWE-20 improper input validation: UTF-8 sequence validation / silent U
- Pinned (vulnerable) commit: d18f6bdfd53a40a572dddced99df296a6ad17009. Published fix: 169eaf36b1116fece5034ee79a7a0ef3f6deedcf.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-480",
 "pattern": "H4",
 "repo": "ultrajson/ultrajson",
 "pinned_commit": "d18f6bdfd53a40a572dddced99df296a6ad17009",
 "protections": [
  "P1: the ASCII-escaping encoder must reject malformed / truncated / out-of-range UTF-8 in string values AND dict keys instead of folding arbitrary bytes into \\uXXXX: Buffer_EscapeStringValidated, reached for values at src/ujson/lib/ultrajsonenc.c:906-914 and for keys at src/ujson/lib/ultrajsonenc.c:690-703.",
  "P2: the JSON string decoder must reject malformed UTF-8 in ujson.loads input instead of mapping invalid byte sequences onto arbitrary codepoints: decode_string, src/ujson/lib/ultrajsondec.c:416-587.",
  "P3: for the ensure_ascii=False path, the only guard is the Python-boundary backstop PyUnicode_DecodeUTF8(ret, retLen, \"surrogatepass\") at src/ujson/python/objToJSON.c:867, applied to the whole encoder output buffer.",
  "P4: reject_bytes=True must raise TypeError for bytes anywhere in the dumped object graph (src/ujson/python/objToJSON.c:426-438 for values; help text at src/ujson/python/ujson.c:61)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/ujson/lib/ultrajsonenc.c:350-368",
    "src/ujson/lib/ultrajsonenc.c:382-404",
    "src/ujson/lib/ultrajsonenc.c:417-432",
    "src/ujson/lib/ultrajsonenc.c:690-703",
    "src/ujson/python/objToJSON.c:426-438"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "src/ujson/lib/ultrajsonenc.c:362-368",
    "src/ujson/lib/ultrajsonenc.c:395-404",
    "src/ujson/lib/ultrajsonenc.c:428-432",
    "src/ujson/lib/ultrajsonenc.c:692",
    "src/ujson/lib/ultrajsonenc.c:908",
    "src/ujson/python/objToJSON.c:429-437"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "src/ujson/lib/ultrajsonenc.c:428-441",
    "src/ujson/lib/ultrajsonenc.c:518-537"
   ],
   "reason_to_dismiss": "The report's example is a bad continuation byte in a 2-byte sequence; the `if (ucs < 0x10000)` test at :434 reads like the range check, so a well-formed 4-byte lead (0xf4 0x90.. and 0xf5-0xf7, all mapped to utflen 4 at :104) is assumed already valid.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/ujson/lib/ultrajsonenc.c:434-439",
    "src/ujson/lib/ultrajsonenc.c:430-432",
    "src/ujson/lib/ultrajsonenc.c:104",
    "src/ujson/lib/ultrajsonenc.c:518-530"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "published_fix_far_site",
   "locations": [
    "src/ujson/lib/ultrajsonenc.c:355",
    "src/ujson/lib/ultrajsonenc.c:388",
    "src/ujson/lib/ultrajsonenc.c:421"
   ],
   "reason_to_dismiss": "Each arm already has a truncation guard (`if (end - io < 1/2/3)`), so the arm looks handled; only the boundary value is wrong, and the extra byte read lands on the NUL that PyBytes always appends.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "neither",
   "evidence": [
    "src/ujson/lib/ultrajsonenc.c:355-360",
    "src/ujson/lib/ultrajsonenc.c:388-393",
    "src/ujson/lib/ultrajsonenc.c:421-426",
    "src/ujson/lib/ultrajsonenc.c:362",
    "src/ujson/lib/ultrajsonenc.c:395-396",
    "src/ujson/lib/ultrajsonenc.c:428"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "src/ujson/lib/ultrajsondec.c:529",
    "src/ujson/lib/ultrajsondec.c:549",
    "src/ujson/lib/ultrajsondec.c:572"
   ],
   "reason_to_dismiss": "The advisory names ujson.dumps() only; loads() is the opposite direction, and the published fix's only decoder footprint is error wording, so the decoder's own validator can be called a separate feature the advisory never covered.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/ujson/lib/ultrajsondec.c:527-535",
    "src/ujson/lib/ultrajsondec.c:544-555",
    "src/ujson/lib/ultrajsondec.c:567-578",
    "src/ujson/lib/ultrajsondec.c:534",
    "src/ujson/lib/ultrajsondec.c:557",
    "src/ujson/lib/ultrajsondec.c:580"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/ujson/lib/ultrajsondec.c:342-355",
    "src/ujson/lib/ultrajsondec.c:519-523"
   ],
   "reason_to_dismiss": "A lone 0x9b in a string body reads as permissive bytes decoding rather than a UTF-8 sequence bug, and the report is about dumping bytes, not about which byte classes may start a character.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/ujson/lib/ultrajsondec.c:352-355",
    "src/ujson/lib/ultrajsondec.c:519-523",
    "src/ujson/lib/ultrajsondec.c:418"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/ujson/lib/ultrajsondec.c:562-583"
   ],
   "reason_to_dismiss": "The report points at the encoder's 4-byte arm; the decoder's own codepoint range was never in the advisory and the published fix left the decoder's logic untouched.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/ujson/lib/ultrajsondec.c:572-582",
    "src/ujson/lib/ultrajsondec.c:359",
    "src/ujson/python/JSONtoObj.c:84"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M6",
   "origin": "uncovered_upstream",
   "locations": [
    "src/ujson/lib/ultrajsonenc.c:929-947",
    "src/ujson/lib/ultrajsonenc.c:945",
    "src/ujson/python/objToJSON.c:152-163",
    "src/ujson/python/objToJSON.c:520-540",
    "src/ujson/python/objToJSON.c:867"
   ],
   "reason_to_dismiss": "The __json__ producer hands raw bytes straight to Buffer_memcpy with no escaping at all, but the PyUnicode_DecodeUTF8 backstop at objToJSON.c:867 already rejects malformed ones, so nothing is silently rewritten end to end.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/ujson/lib/ultrajsonenc.c:938-947",
    "src/ujson/python/objToJSON.c:537-539",
    "src/ujson/python/objToJSON.c:867"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "src/ujson/lib/ultrajsonenc.c:191-204",
    "src/ujson/lib/ultrajsonenc.c:296-299",
    "src/ujson/lib/ultrajsonenc.c:699-703",
    "src/ujson/lib/ultrajsonenc.c:917-923",
    "src/ujson/lib/ultrajson.h:243-245",
    "src/ujson/lib/Makefile:13-15"
   ],
   "reason_to_dismiss": "forceASCII=0 is documented as a raw passthrough (\"UTF-8 or what ever charset strings are brought as\", ultrajson.h:244); in Python it is chosen by ensure_ascii=False and its output is still decoded strictly at objToJSON.c:867, while the embeddable libujson.a entry via JSON_EncodeObject cannot be reached from pytest.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/ujson/lib/ultrajson.h:243-245",
    "src/ujson/lib/ultrajsonenc.c:204",
    "src/ujson/lib/ultrajsonenc.c:296",
    "src/ujson/lib/ultrajsonenc.c:917-923",
    "src/ujson/python/objToJSON.c:727-730",
    "src/ujson/python/objToJSON.c:867",
    "setup.py:42-51"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "src/ujson/python/objToJSON.c:214-242",
    "src/ujson/python/objToJSON.c:220-224",
    "src/ujson/python/objToJSON.c:429-437"
   ],
   "reason_to_dismiss": "reject_bytes is a bytes-policy switch, not the UTF-8 property in the advisory; bytes keys have always been coerced verbatim by Dict_convertKey and the report says nothing about them.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "easy",
   "type": "deepseek",
   "evidence": [
    "src/ujson/python/objToJSON.c:220-224",
    "src/ujson/python/objToJSON.c:429-433",
    "src/ujson/python/ujson.c:61",
    "src/ujson/lib/ultrajsonenc.c:811-815"
   ]
  },
  {
   "id": "T10",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "src/ujson/lib/ultrajsonenc.c:407-412",
    "src/ujson/lib/ultrajsonenc.c:434-439",
    "src/ujson/lib/ultrajsondec.c:539-558",
    "src/ujson/python/objToJSON.c:137",
    "tests/test_ujson.py:643-654",
    "tests/test_ujson.py:684-686"
   ],
   "reason_to_dismiss": "A strict RFC-3629 validator calls ED A0 80 malformed, so a solver can read the surrogate expectations as legacy quirks to update rather than as a value the new guard must keep accepting.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "tests/test_ujson.py:648-650",
    "tests/test_ujson.py:652-654",
    "tests/test_ujson.py:686",
    "src/ujson/python/objToJSON.c:137",
    "src/ujson/python/objToJSON.c:218",
    "src/ujson/lib/ultrajsonenc.c:407-412"
   ]
  },
  {
   "id": "T11",
   "mechanism": "M1",
   "origin": "injection_room",
   "locations": [
    "src/ujson/python/objToJSON.c:214-224",
    "src/ujson/lib/ultrajsonenc.c:690-703",
    "src/ujson/lib/ultrajsonenc.c:811-815"
   ],
   "reason_to_dismiss": "The reported repro is a top-level bytes value, so a guard added where the report lands (objToJSON.c:426-438) is assumed to cover keys too; bytes keys take the Dict_convertKey route and are exempt from reject_bytes anyway.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "easy",
   "type": "deepseek",
   "evidence": [
    "src/ujson/python/objToJSON.c:220-224",
    "src/ujson/lib/ultrajsonenc.c:690-696",
    "src/ujson/lib/ultrajsonenc.c:811-815"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T3",
   "T11"
  ],
  [
   "T2"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ],
  [
   "T9"
  ],
  [
   "T10"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "T2 is masked by T1: once continuation bytes are validated, a broad 'malformed UTF-8 raises' test passes, and only a well-formed but >U+10FFFF 4-byte sequence (0xf4 0x90 0x80 0x80, or a 0xf5-0xf7 lead) still shows the missing range check.",
   "T3 is masked by T1: with a continuation test added, a sequence truncated at end-of-buffer reads the trailing NUL, fails the continuation test and raises, so the one-byte-short bounds never show in a behavioural test.",
   "T5 and T6 are masked by T4: after the continuation mask is fixed, most malformed decoder input raises, and only a lone 0x80-0xbf lead byte or a well-formed >U+10FFFF sequence still decodes.",
   "T11 is exposed by where T1 is fixed: a guard placed only in the bytes-value branch at objToJSON.c:426-438 makes the reported value repro pass while bytes dict keys stay unvalidated."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T10",
   "what": "The natural strict-UTF-8 continuation/range fix also rejects D800-DFFF; that breaks tests/test_ujson.py:643-650, which require dumps(b'\\xed\\xa0\\x80', reject_bytes=False) to yield \"\\ud800\" (and the same bytes as a dict key). The guard must accept ED A0 80-ED BF BF."
  },
  {
   "a": "T4",
   "b": "T10",
   "what": "A strict decoder that rejects surrogate codepoints breaks tests/test_ujson.py:684-686, which require loads(b'\"\\xed\\xa0\\x80\"') to return a lone surrogate."
  },
  {
   "a": "T5",
   "b": "T10",
   "what": "Same as T4 on the lead-byte side: a table that rejects 0xed, or any rule that rejects surrogate codepoints, breaks the decoder surrogate round-trip at tests/test_ujson.py:686."
  },
  {
   "a": "T8",
   "b": "T10",
   "what": "Mirroring the validated checks into Buffer_EscapeStringUnvalidated (or decoding ensure_ascii=False output with a strict codec instead of surrogatepass) breaks tests/test_ujson.py:652-654, which require ensure_ascii=False to emit raw lone-surrogate bytes."
  },
  {
   "a": "T11",
   "b": "T10",
   "what": "A key-side strict-UTF-8 check in Dict_convertKey (a natural place to add validation, objToJSON.c:214-242) rejects the UTF-8-encoded surrogate keys used at tests/test_ujson.py:648-650."
  }
 ],
 "fairness_risks": [
  "Must-keep value: UTF-8-encoded lone surrogates (ED A0 80 / ED BF BF) must stay accepted and be escaped to \\ud800 / \\udfff - tests/test_ujson.py:643-650 (encoder, bytes keys and values) and tests/test_ujson.py:684-686 (decoder, bytes input). Strict RFC-3629 rejects the surrogate range, so 'the security rule' and the pinned test suite contradict each other unless the rule is explicitly surrogate-permitting.",
  "Must-keep value: ensure_ascii=False must keep writing raw surrogate bytes for str input (tests/test_ujson.py:652-654); any validation added to the ensure_ascii=False branch that is stricter than PyUnicode_DecodeUTF8(..., \"surrogatepass\") breaks it.",
  "Error type is load-bearing: every encoder-side SetError becomes PyExc_OverflowError (src/ujson/python/objToJSON.c:849-855; pinned test tests/test_ujson.py:374-377). A solver who raises UnicodeDecodeError or ValueError from objToJSON is defensible but would fail any test that matches the existing exception type or message.",
  "Legitimate input shape: all valid non-ASCII UTF-8 must keep round-tripping (tests/test_ujson.py:1140-1155, 510-514); a rule that rejects bytes >= 0x80 or any multi-byte sequence is over-broad.",
  "Legitimate input shape: ujson.loads accepts any C-contiguous buffer, including array.array and memoryview (src/ujson/python/JSONtoObj.c:204-217; tests/test_ujson.py:1468-1481 and 1504-1513). A decoder fix that requires NUL termination, or that pre-decodes the whole buffer with a Python codec, must not drop those input types.",
  "Legitimate input shape: bytes dict keys with reject_bytes=False must keep working (tests/test_ujson.py:648-650 passes a bytes key), so a key-side guard must be UTF-8 validation rather than a bytes ban."
 ],
 "effort_minutes": 60,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T3",
   "T11",
   "T2",
   "T4",
   "T5",
   "T10"
  ],
  "why": "Five independent judgements across two implementations, each with a different dismissal. G1{T1,T3,T11} is the advisory surface, but it still holds three shapes: 2/3/4-byte continuation bytes, an end-of-buffer truncation whose guard is already there but one byte short, and the bytes-dict-key entry that bypasses the bytes-value branch where the report lands. G2{T2} needs a second rule (codepoint range) in an arm that already looks guarded by the overlong test. G3{T4} is the same class in the separate decoder implementation, where a guard exists but tests the wrong bit mask ((oct & 0x80) != 0x80) and whose only published-fix footprint is error wording - the strongest dismissable reason. G4{T5} needs the lead-byte table changed, which the mask fix does not touch. G9{T10} is the M11 keep-working value that punishes the over-strict RFC-3629 fix MiMo tends to write. The four dismissal arguments are distinct: 'it is the reported repro', 'the range guard is already there', 'loads() is the other direction and the fix only relabelled messages', and 'surrogates must survive'. T6, T7, T8 and T9 are deliberately left out: T6's end-to-end behaviour depends on unverified PyUnicode_FromKindAndData handling of >U+10FFFF; T7 and T8 are already closed end to end by the PyUnicode_DecodeUTF8 backstop, so grading a change there would reward a false positive (and T8's libujson.a leg is not reachable from pytest); T9 is a reject_bytes policy gap, not the advisory's UTF-8 property."
 },
 "unverified": [
  "The full advisory text was not available; whether GHSA-3J69-69WJ-XQX2 / CVE-2026-54911 is meant to cover ujson.loads as well as ujson.dumps is judged from the screener summary, the landing point and the code, not from the report.",
  "fix.diff was not available in the pinned worktree, so whether the published fix actually adds the encoder >U+10FFFF check (T2) and the corrected end-of-buffer bounds (T3) is inferred from the screener's fix_sites and O6 input-shape list, not read.",
  "Whether CPython's PyUnicode_FromKindAndData (src/ujson/python/JSONtoObj.c:84) rejects or silently stores a >U+10FFFF codepoint was not verified (no build/run), so T6's end-to-end observable behaviour (raise vs a broken str) is unknown.",
  "Whether the hidden tests assert exact hyphenated validator message text (e.g. the new continuation messages, or the decoder's 'Overlong 3 byte ... when encoding string' wording at src/ujson/lib/ultrajsondec.c:557 that the published fix is said to have relabelled) is unknown; a message-only hunk is not a trap under the mechanism rules but would be graded if asserted.",
  "No git history access in this session: whether the existing overlong checks (ultrajsonenc.c:371-376, 407-412, 434-439) and 'Unterminated UTF-8 sequence' bounds came from an earlier fix commit - which would make this an H3b incomplete-fix shape rather than a pure H4 - could not be confirmed.",
  "The extension was not compiled and no tests were run; all behaviour is read off the C sources. That a new encoder SetError surfaces as PyExc_OverflowError follows from src/ujson/python/objToJSON.c:849-855 and matches the pinned expectation at tests/test_ujson.py:374-377, but was not executed.",
  "The decoder's reliance on a trailing NUL (it reads *ds->start / *inputOffset without an end check at ultrajsondec.c:418, 521, 547, 570) is only safe for NUL-terminated inputs; whether array.array/memoryview inputs (accepted at JSONtoObj.c:204-217, exercised at tests/test_ujson.py:1478-1481) read out of bounds was not measured, and it is a separate bounds family rather than the UTF-8 property.",
  "Whether the encoder's one-byte-over reads at ultrajsonenc.c:362/395/428 stay inside the allocation depends on the NUL that PyBytes and PyUnicode_AsEncodedString append; this holds for the Python bindings but not for an arbitrary caller of the C API, and was not checked under ASAN."
 ]
}
  ```
- Published fix sites:   - src/ujson/lib/ultrajsonenc.c:350-368 — T1 M4 (reason to dismiss: none)
  - src/ujson/lib/ultrajsonenc.c:382-404 — T1 M4 (reason to dismiss: none)
  - src/ujson/lib/ultrajsonenc.c:417-432 — T1 M4 (reason to dismiss: none)
  - src/ujson/lib/ultrajsonenc.c:690-703 — T1 M4 (reason to dismiss: none)
  - src/ujson/python/objToJSON.c:426-438 — T1 M4 (reason to dismiss: none)
  - src/ujson/lib/ultrajsonenc.c:428-441 — T2 M4 (reason to dismiss: The report's example is a bad continuation byte in a 2-byte sequence; the `if (ucs < 0x10000)` test at :434 reads like the range check, so a well-formed 4-byte lead (0xf4 0x90.. and 0xf5-0xf7, all mapped to utflen 4 at :104) is assumed already valid.)
  - src/ujson/lib/ultrajsonenc.c:518-537 — T2 M4 (reason to dismiss: The report's example is a bad continuation byte in a 2-byte sequence; the `if (ucs < 0x10000)` test at :434 reads like the range check, so a well-formed 4-byte lead (0xf4 0x90.. and 0xf5-0xf7, all mapped to utflen 4 at :104) is assumed already valid.)
  - src/ujson/lib/ultrajsonenc.c:355 — T3 M8 (reason to dismiss: Each arm already has a truncation guard (`if (end - io < 1/2/3)`), so the arm looks handled; only the boundary value is wrong, and the extra byte read lands on the NUL that PyBytes always appends.)
  - src/ujson/lib/ultrajsonenc.c:388 — T3 M8 (reason to dismiss: Each arm already has a truncation guard (`if (end - io < 1/2/3)`), so the arm looks handled; only the boundary value is wrong, and the extra byte read lands on the NUL that PyBytes always appends.)
  - src/ujson/lib/ultrajsonenc.c:421 — T3 M8 (reason to dismiss: Each arm already has a truncation guard (`if (end - io < 1/2/3)`), so the arm looks handled; only the boundary value is wrong, and the extra byte read lands on the NUL that PyBytes always appends.)
  - src/ujson/lib/ultrajsonenc.c:407-412 — T10 M11 (reason to dismiss: A strict RFC-3629 validator calls ED A0 80 malformed, so a solver can read the surrogate expectations as legacy quirks to update rather than as a value the new guard must keep accepting.)
  - src/ujson/lib/ultrajsonenc.c:434-439 — T10 M11 (reason to dismiss: A strict RFC-3629 validator calls ED A0 80 malformed, so a solver can read the surrogate expectations as legacy quirks to update rather than as a value the new guard must keep accepting.)
  - src/ujson/lib/ultrajsondec.c:539-558 — T10 M11 (reason to dismiss: A strict RFC-3629 validator calls ED A0 80 malformed, so a solver can read the surrogate expectations as legacy quirks to update rather than as a value the new guard must keep accepting.)
  - src/ujson/python/objToJSON.c:137 — T10 M11 (reason to dismiss: A strict RFC-3629 validator calls ED A0 80 malformed, so a solver can read the surrogate expectations as legacy quirks to update rather than as a value the new guard must keep accepting.)
  - tests/test_ujson.py:643-654 — T10 M11 (reason to dismiss: A strict RFC-3629 validator calls ED A0 80 malformed, so a solver can read the surrogate expectations as legacy quirks to update rather than as a value the new guard must keep accepting.)
  - tests/test_ujson.py:684-686 — T10 M11 (reason to dismiss: A strict RFC-3629 validator calls ED A0 80 malformed, so a solver can read the surrogate expectations as legacy quirks to update rather than as a value the new guard must keep accepting.)
- Uncovered routes to confirm (pattern B):   - src/ujson/lib/ultrajsondec.c:529 — T4 M2 (reason to dismiss: The advisory names ujson.dumps() only; loads() is the opposite direction, and the published fix's only decoder footprint is error wording, so the decoder's own validator can be called a separate feature the advisory never covered.)
  - src/ujson/lib/ultrajsondec.c:549 — T4 M2 (reason to dismiss: The advisory names ujson.dumps() only; loads() is the opposite direction, and the published fix's only decoder footprint is error wording, so the decoder's own validator can be called a separate feature the advisory never covered.)
  - src/ujson/lib/ultrajsondec.c:572 — T4 M2 (reason to dismiss: The advisory names ujson.dumps() only; loads() is the opposite direction, and the published fix's only decoder footprint is error wording, so the decoder's own validator can be called a separate feature the advisory never covered.)
  - src/ujson/lib/ultrajsondec.c:342-355 — T5 M4 (reason to dismiss: A lone 0x9b in a string body reads as permissive bytes decoding rather than a UTF-8 sequence bug, and the report is about dumping bytes, not about which byte classes may start a character.)
  - src/ujson/lib/ultrajsondec.c:519-523 — T5 M4 (reason to dismiss: A lone 0x9b in a string body reads as permissive bytes decoding rather than a UTF-8 sequence bug, and the report is about dumping bytes, not about which byte classes may start a character.)
  - src/ujson/lib/ultrajsondec.c:562-583 — T6 M4 (reason to dismiss: The report points at the encoder's 4-byte arm; the decoder's own codepoint range was never in the advisory and the published fix left the decoder's logic untouched.)
  - src/ujson/lib/ultrajsonenc.c:929-947 — T7 M6 (reason to dismiss: The __json__ producer hands raw bytes straight to Buffer_memcpy with no escaping at all, but the PyUnicode_DecodeUTF8 backstop at objToJSON.c:867 already rejects malformed ones, so nothing is silently rewritten end to end.)
  - src/ujson/lib/ultrajsonenc.c:945 — T7 M6 (reason to dismiss: The __json__ producer hands raw bytes straight to Buffer_memcpy with no escaping at all, but the PyUnicode_DecodeUTF8 backstop at objToJSON.c:867 already rejects malformed ones, so nothing is silently rewritten end to end.)
  - src/ujson/python/objToJSON.c:152-163 — T7 M6 (reason to dismiss: The __json__ producer hands raw bytes straight to Buffer_memcpy with no escaping at all, but the PyUnicode_DecodeUTF8 backstop at objToJSON.c:867 already rejects malformed ones, so nothing is silently rewritten end to end.)
  - src/ujson/python/objToJSON.c:520-540 — T7 M6 (reason to dismiss: The __json__ producer hands raw bytes straight to Buffer_memcpy with no escaping at all, but the PyUnicode_DecodeUTF8 backstop at objToJSON.c:867 already rejects malformed ones, so nothing is silently rewritten end to end.)
  - src/ujson/python/objToJSON.c:867 — T7 M6 (reason to dismiss: The __json__ producer hands raw bytes straight to Buffer_memcpy with no escaping at all, but the PyUnicode_DecodeUTF8 backstop at objToJSON.c:867 already rejects malformed ones, so nothing is silently rewritten end to end.)
  - src/ujson/lib/ultrajsonenc.c:191-204 — T8 M1 (reason to dismiss: forceASCII=0 is documented as a raw passthrough ("UTF-8 or what ever charset strings are brought as", ultrajson.h:244); in Python it is chosen by ensure_ascii=False and its output is still decoded strictly at objToJSON.c:867, while the embeddable libujson.a entry via JSON_EncodeObject cannot be reached from pytest.)
  - src/ujson/lib/ultrajsonenc.c:296-299 — T8 M1 (reason to dismiss: forceASCII=0 is documented as a raw passthrough ("UTF-8 or what ever charset strings are brought as", ultrajson.h:244); in Python it is chosen by ensure_ascii=False and its output is still decoded strictly at objToJSON.c:867, while the embeddable libujson.a entry via JSON_EncodeObject cannot be reached from pytest.)
  - src/ujson/lib/ultrajsonenc.c:699-703 — T8 M1 (reason to dismiss: forceASCII=0 is documented as a raw passthrough ("UTF-8 or what ever charset strings are brought as", ultrajson.h:244); in Python it is chosen by ensure_ascii=False and its output is still decoded strictly at objToJSON.c:867, while the embeddable libujson.a entry via JSON_EncodeObject cannot be reached from pytest.)
  - src/ujson/lib/ultrajsonenc.c:917-923 — T8 M1 (reason to dismiss: forceASCII=0 is documented as a raw passthrough ("UTF-8 or what ever charset strings are brought as", ultrajson.h:244); in Python it is chosen by ensure_ascii=False and its output is still decoded strictly at objToJSON.c:867, while the embeddable libujson.a entry via JSON_EncodeObject cannot be reached from pytest.)
  - src/ujson/lib/ultrajson.h:243-245 — T8 M1 (reason to dismiss: forceASCII=0 is documented as a raw passthrough ("UTF-8 or what ever charset strings are brought as", ultrajson.h:244); in Python it is chosen by ensure_ascii=False and its output is still decoded strictly at objToJSON.c:867, while the embeddable libujson.a entry via JSON_EncodeObject cannot be reached from pytest.)
  - src/ujson/lib/Makefile:13-15 — T8 M1 (reason to dismiss: forceASCII=0 is documented as a raw passthrough ("UTF-8 or what ever charset strings are brought as", ultrajson.h:244); in Python it is chosen by ensure_ascii=False and its output is still decoded strictly at objToJSON.c:867, while the embeddable libujson.a entry via JSON_EncodeObject cannot be reached from pytest.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T3, T11, T2, T4, T5, T10. Why: Five independent judgements across two implementations, each with a different dismissal. G1{T1,T3,T11} is the advisory surface, but it still holds three shapes: 2/3/4-byte continuation bytes, an end-of-buffer truncation whose guard is already there but one byte short, and the bytes-dict-key entry that bypasses the bytes-value branch where the report lands. G2{T2} needs a second rule (codepoint range) in an arm that already looks guarded by the overlong test. G3{T4} is the same class in the separate decoder implementation, where a guard exists but tests the wrong bit mask ((oct & 0x80) != 0x80) and whose only published-fix footprint is error wording - the strongest dismissable reason. G4{T5} needs the lead-byte table changed, which the mask fix does not touch. G9{T10} is the M11 keep-working value that punishes the over-strict RFC-3629 fix MiMo tends to write. The four dismissal arguments are distinct: 'it is the reported repro', 'the range guard is already there', 'loads() is the other direction and the fix only relabelled messages', and 'surrogates must survive'. T6, T7, T8 and T9 are deliberately left out: T6's end-to-end behaviour depends on unverified PyUnicode_FromKindAndData handling of >U+10FFFF; T7 and T8 are already closed end to end by the PyUnicode_DecodeUTF8 backstop, so grading a change there would reward a false positive (and T8's libujson.a leg is not reachable from pytest); T9 is a reject_bytes policy gap, not the advisory's UTF-8 property. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Must-keep value: UTF-8-encoded lone surrogates (ED A0 80 / ED BF BF) must stay accepted and be escaped to \ud800 / \udfff - tests/test_ujson.py:643-650 (encoder, bytes keys and values) and tests/test_ujson.py:684-686 (decoder, bytes input). Strict RFC-3629 rejects the surrogate range, so 'the security rule' and the pinned test suite contradict each other unless the rule is explicitly surrogate-permitting. | Must-keep value: ensure_ascii=False must keep writing raw surrogate bytes for str input (tests/test_ujson.py:652-654); any validation added to the ensure_ascii=False branch that is stricter than PyUnicode_DecodeUTF8(..., "surrogatepass") breaks it. | Error type is load-bearing: every encoder-side SetError becomes PyExc_OverflowError (src/ujson/python/objToJSON.c:849-855; pinned test tests/test_ujson.py:374-377). A solver who raises UnicodeDecodeError or ValueError from objToJSON is defensible but would fail any test that matches the existing exception type or message. | Legitimate input shape: all valid non-ASCII UTF-8 must keep round-tripping (tests/test_ujson.py:1140-1155, 510-514); a rule that rejects bytes >= 0x80 or any multi-byte sequence is over-broad. | Legitimate input shape: ujson.loads accepts any C-contiguous buffer, including array.array and memoryview (src/ujson/python/JSONtoObj.c:204-217; tests/test_ujson.py:1468-1481 and 1504-1513). A decoder fix that requires NUL termination, or that pre-decodes the whole buffer with a Python codec, must not drop those input types. | Legitimate input shape: bytes dict keys with reject_bytes=False must keep working (tests/test_ujson.py:648-650 passes a bytes key), so a key-side guard must be UTF-8 validation rather than a bytes ban.. Conflicts the reader found: The natural strict-UTF-8 continuation/range fix also rejects D800-DFFF; that breaks tests/test_ujson.py:643-650, which require dumps(b'\xed\xa0\x80', reject_bytes=False) to yield "\ud800" (and the same bytes as a dict key). The guard must accept ED A0 80-ED BF BF. | A strict decoder that rejects surrogate codepoints breaks tests/test_ujson.py:684-686, which require loads(b'"\xed\xa0\x80"') to return a lone surrogate. | Same as T4 on the lead-byte side: a table that rejects 0xed, or any rule that rejects surrogate codepoints, breaks the decoder surrogate round-trip at tests/test_ujson.py:686. | Mirroring the validated checks into Buffer_EscapeStringUnvalidated (or decoding ensure_ascii=False output with a strict codec instead of surrogatepass) breaks tests/test_ujson.py:652-654, which require ensure_ascii=False to emit raw lone-surrogate bytes. | A key-side strict-UTF-8 check in Dict_convertKey (a natural place to add validation, objToJSON.c:214-242) rejects the UTF-8-encoded surrogate keys used at tests/test_ujson.py:648-650.

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

## Environment (`tasks/stk-ultrajson-480/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-ultrajson-480/instruction.md`)
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

## Tests (`tasks/stk-ultrajson-480/tests/`)
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
- **Wrong-fix patches** go in `build/stk-ultrajson-480/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-ultrajson-480/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-ultrajson-480/manifest.json`:**
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

**Also in `build/stk-ultrajson-480/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-ultrajson-480 --only static
python3 -I common/gate/gate.py stk-ultrajson-480 --only nop
python3 -I common/gate/gate.py stk-ultrajson-480 --only oracle
python3 -I common/gate/gate.py stk-ultrajson-480 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-ultrajson-480/`;
  - edit only `tasks/stk-ultrajson-480/`, `build/stk-ultrajson-480/` and, for pattern B, the register;
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


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-480.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-ultrajson-480`. Control task slug: `stk-ultrajson-480-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-480.json`.
