# handlebars.js-s2 — build notes

Started (UTC): 2026-10-26T12:33Z
Finished (UTC): TBD

Task: build-v1, pattern A+B, track injected.
Advisory: GHSA-8R5X-FM3F-WHWJ / CVE-2026-106446 (code injection, CWE-94, through AST type
confusion, CWE-843). Pinned 0fcf25c63038b43e78e17adbf029cf073e80554d, published fix
703fdcc5fd6cc8d1cc0c33cc19de40c467c4b8d2.

## Plan (written before building)

### Product story and the one property

The project is a JavaScript template engine. `compile`/`precompile` accept either template text
or a pre-parsed AST (a plain object/JSON structure); tools and applications cache parsed
templates in that form and compile them later, including from storage users can write to.
The document is data, never code.

Property (stated once, in the report):
> No value carried by a supplied syntax tree may become executable JavaScript. Whenever the
> library turns a document into template code, every value it writes into that code is either
> (a) inside a correctly quoted string literal that reads back as exactly the value, or (b) a
> literal whose value is exactly the kind its position declares. A document whose value cannot
> be represented that way is refused with an ordinary error, and nothing derived from it runs.
> This holds for every value anywhere in the document, whatever its type or spelling, and at
> every public entry point that turns a document into code.

### Levers, each with a different reason to dismiss

Main lever (how-type, shape a plausible check mishandles):
- T2 `param-depth` — `pushParam` reads `depth` from **every** parameter node, not only from a path
  node, and in string-parameter mode the value is interpolated into `depths[...]` in generated
  code. A check keyed on the node type ("a path has a depth; a literal does not") misses it.
  where: lib/handlebars/compiler/compiler.js:411-453 (pushParam), javascript-compiler.js:1107-1113
  (contextName). Reason to dismiss: a literal node has no depth, and paths are already validated.

More levers:
- T1 `blockparams-length` — `Compiler.Program` keeps `program.blockParams.length`, which
  `programExpression` interpolates raw into `container.program(...)`. Reason to dismiss: block
  params are a list of names and only the length is used, so it cannot carry code.
  where: compiler.js:103-118, javascript-compiler.js:959-970.
- T3 `param-value` — in string-parameter mode `pushParam`/`pushStringParam` emits any non-string
  param value as a raw literal; `value` or `original` can be an array/object. Reason to dismiss:
  `original` is source text used for lookups, not something the compiler prints.
  where: compiler.js:411-430, javascript-compiler.js:594-607.
- T4 `pipeline` (Pattern A/B far site) — the parser-level AST check (pinned base.js) never runs
  when an application assembles the exported compiler stages itself; the published fix moves the
  checks into the compiler and therefore covers it, while any fix that only extends the parser
  check does not. Reason to dismiss: the documented convenience entry points are compile and
  precompile, so the stages read as internal plumbing. where: lib/handlebars.js:20-32,
  compiler.js:470-520.
- T5 `bigint` (injected sibling) — a maintained big-integer literal node whose decimal text is
  concatenated with the `n` suffix into generated code. Reason to dismiss: the value is a string
  and "strings are quoted" — but this is an integer-literal position, and a type-only check
  still passes attacker text. where: compiler.js new `BigIntLiteral` handler,
  javascript-compiler.js new `pushBigInt`.
- T6 `partial-indent` (injected sibling) — partial indentation is written into the generated
  options literal by manual quoting, assuming the whitespace pass only produces spaces and tabs.
  The whitespace pass is a producer that runs after the parser-level check and does not touch a
  non-standalone partial; a hand-built AST supplies the indent directly. Reason to dismiss: the
  indentation comes from the whitespace pass, which can only produce whitespace.
  where: javascript-compiler.js invokePartial.

Coupled must-keep-working behaviours (functional, all true on the pinned code):
- number and boolean parameters in string-parameter mode still reach helpers as numbers/booleans
  (T2, T3);
- path parameters are still normalised (`./a/b` -> `a.b`) in string-parameter mode (T3);
- block parameters still bind (T1);
- indented partials still render with their indentation, including a hand-built AST whose indent
  is spaces/tabs (T6);
- a big-integer literal AST still reaches a helper as a BigInt (T5);
- a very large numeric literal in template text still renders Infinity (guards against an
  over-broad finiteness check; T2/T3);
- ordinary string templates and ordinary full ASTs render exactly as today (all levers).

Legitimate magnitude next to the attack magnitude: a 400-digit numeric literal (Infinity) and a
BigInt decimal text of 100+ digits are ordinary values; only text that is not an integer is
refused.

### Injected sibling candidates found (all of them), and why the two picks won

From the screener's O8/O8b leads plus a search of lib/:
1. ast.js:16-26 derived-attribute helper reading parts/original before validation — only causes a
   crash/wrong classification, never reaches generated code; not covered by a property about code
   emission. Rejected.
2. javascript-compiler.js:1107-1113 a second `contextName`-style interpolation — any new *caller*
   would also need a new AST field; T2 already owns this sink, and adding a second raw sink there
   duplicates the same concept. Rejected as a sibling (kept as the sink for T2).
3. whitespace-control.js:192-232 post-check rewrite of node values — the values it writes are
   content text, which the compiler quotes; no raw sink. Rejected as a whole, but its output is
   the producer for T6 (a hand-built indent bypasses it).
4. javascript-compiler.js:658-660 new pushLiteral-style opcode — picked as T5 (BigInt literal):
   a realistic new literal kind, emitted raw, and a type-only check is insufficient because the
   value is text.
5. New fast path in `internalNameLookup` keyed on `name.indexOf('.')` — an array name would pass
   and be joined raw, but it also breaks legitimate non-identifier part names (project tests
   catch it), so it is not code a maintainer could have left. Rejected.
6. A new opcode interpolating a numeric field beyond depth/length — no additional AST-controlled
   numeric field exists; would require inventing a field. Rejected.
7. `PartialStatement.indent` raw emission (T6) — picked: real producer off the check's path
   (whitespace-control), real consumer (runtime partial indentation), and the assumption is true
   for parsed templates while false for hand-built ASTs.

Why T5 and T6 beat the others: both are how-type (T5 needs understanding that integer text in a
literal position is still code; T6 needs understanding that the whitespace pass is the only thing
that makes an indent trustworthy), both are far from the report's landing point (a new node type
and the partial runtime path), and each has a distinct dismissal. The others were either
duplicates of the same sink (2), outside the property (1, 3), or not realistic (5, 6).

### Sites, routes, shapes the security tests cover

- compile(ast) and precompile(ast) with a crafted blockParams length (T1).
- compile(ast, {stringParams:true}) with a non-path parameter carrying a text depth (T2);
  same shape through precompile so the eager path is covered.
- compile(ast, {stringParams:true}) with an array `original` on a path parameter (T3), and with an
  array `value` on a string literal parameter (T3, second shape).
- The exported compiler-stage route with a text path depth and with a crafted blockParams length
  (T4, the Pattern B route; confirmed behaviourally on the pinned copy).
- compile(ast) with a big-integer literal whose decimal text carries code (T5).
- compile(ast) with a partial whose indent carries code (T6).

### Pattern B register

One row: the exported compiler-stage route (lib/handlebars.js:28-29). Confirmed behaviourally:
on the pinned copy `new Compiler().compile(ast)` + `new JavaScriptCompiler().compile(env)`
compiles a path depth that the parser-level check would reject, and the generated code runs it.
The published fix protects it because the checks moved into the compiler; a fix that only extends
the parser check does not.

## Verification log (filled during the build)

- Pinned build: `npm install` + `grunt parser node` works on Node 20.19.2; the project's specs
  (basic, blocks, partials, string-params, track-ids, security, ast, compiler, whitespace-control,
  subexpressions, data, strict, precompiler, helpers, regressions, runtime) pass: 516 passing.
- Reproduced on the pinned+injected tree: blockParams length (marker runs), non-path param depth
  in stringParams (marker runs), array original (marker runs), stage route (marker runs),
  BigInt text (marker runs), partial indent (marker runs).
- Oracle (published fix + sibling fixes): all six blocked; the chosen project spec subset passes
  (512 passing) when spec/compiler.js is excluded (its four parser-check tests assert the old
  messages and are superseded by the published fix; not used in grading).
- Not a security route: StringLiteral.value as a number, ContentStatement value as a number,
  Hash pairs as an object — on the pinned copy these render quoted/empty or crash before code is
  emitted, so they do not violate the property and are not graded as attacks.

## Unknowns / unverified

- Did not read upstream after the fix commit beyond the cherry-picked commit.
- One Oracle trial run per stage was not repeated for flakiness yet (gate does 3).
