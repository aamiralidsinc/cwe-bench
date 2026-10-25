# Stacking upgrade prompt (instruction-only rewrite of a built stacked task), v2, 2026-10-24

**v2:** rule 3 added (keep behaviour the fix itself must add; comfyui lost its carry-over contract in v1).

**What it is:** the prompt `stacking/run_upgrade_stack.sh` gives the upgrade agent. It rewrites ONE
built stacked task's `instruction.md` so it passes build rule 7 (the one-bug test) of
`STACKING-BUILD-ADDENDUM.md` v2. Nothing else changes: no tests, no reference fix, no manifest, no
image, so no rebuild and no container gate. It is the stacking form of `builder/UPGRADE-PROMPT.md`
(the sibling upgrade), cut down to its instruction step, because stacked tasks already have their
traps and tests. `run_stack_pipeline.sh` is not involved.

---8<---

You are UPGRADING the report (`instruction.md`) of ONE already-built security-fix task. The task is
already valid and gated: its code, tests and reference fix stay exactly as they are. Only the report
changes. Project root: {{ROOT}}. Task slug: {{SLUG}}.

**Why.** The solver sees only `instruction.md` and the repository. The task hides several traps the
solver must find on its own: routes, forms, sources, a second implementation, coupled values. The
current report lists many of them, sentence by sentence, so the task reads as a checklist and is
solved by working through it. The rewritten report must state the goal and the general property, and
must not point at any hidden trap.

**Read:**
- `{{ROOT}}/tasks/{{SLUG}}/instruction.md` (the report you rewrite);
- `{{ROOT}}/build/{{SLUG}}/manifest.json`: the `traps` list (`id`, `origin`, `shape`, `where`,
  `coupled_functional_tests`) and `leak_terms`. The trap with origin `advisory_route` is the reported
  bug; every other trap is hidden;
- `{{ROOT}}/build/{{SLUG}}/listing.json`, if present: a reviewer's labels for how the current report
  covers each trap (NAMED / DESCRIBED / GENERAL / ABSENT), with the phrase behind each label. Every
  NAMED or DESCRIBED hidden trap there must end up GENERAL or ABSENT;
- the files under `{{ROOT}}/tasks/{{SLUG}}/tests/`, read-only, only to check that no rule you write
  forbids a value a functional test keeps working.

**Rules for the new report:**
1. **The one-bug test.** For every sentence ask: "would this sentence be here if the task had only
   the advisory's own route?" If not, delete it or replace it with general wording. That removes forms
   ("in every form it can be named"), timing ("and again when the call connects"), sources
   ("whichever response supplies it"), encodings, aliases, second implementations, lists of
   operations or resources, scope-widening clauses over parts of the system only hidden traps occupy
   ("whatever the component involved"), and example values in keep-working lines.
2. **Keep:** the title and the impact example of the advisory's own route (the only route that may be
   shown); one general property per distinct protection, phrased over the protected data or outcome;
   the general contracts that hold for every route: the refusal form (for example "a client error,
   with no effect"), an operator opt-in if the task has one, "everything that works today keeps
   working", and the constraints section ("fix the problem and its close variants", "do not look up
   the upstream fix", "do not special-case the example").
3. **Keep what the fix itself must add on the advisory's own route.** A sentence that states new
   behaviour the correct fix must have for the reported bug (for example: existing data is carried
   over to the new place without being weakened, or a value the operator saved is not overwritten
   by an enforced one) passes the one-bug test, because the one-bug task needs it too. Keep it, in
   general terms. "Everything that works today keeps working" never covers it: that behaviour does
   not exist today. And never write a rule that forbids it (2026-10-24: an upgrade dropped such a
   carry-over contract and wrote "take its state only from there", so a literal fix failed).
4. **Coupled values** are covered ONLY by the general keep-working sentence. Never name or describe
   them. If a security rule, read literally, would forbid a value a functional test keeps working,
   reword the security rule over its protected outcome; never add an exception that names the value.
5. **Add nothing specific.** No new identifier, file, function, endpoint, field, value or count. No
   word from `leak_terms`. The property must still cover every hidden trap when read literally (so the
   task stays fair), without pointing at any of them.
6. **Keep it short:** the goal in a few lines, the property, the general contracts. Same section
   layout and tone as the current report.

**Do:** edit only `{{ROOT}}/tasks/{{SLUG}}/instruction.md`. Do not change any other file, do not
create files, and do not run anything. Do not touch the control task; the launcher copies your report
to it.

**Report, under 200 words:** the framing before and after (one line each), the sentences you removed
or generalised (one short line each), and any hidden trap you could not cover generally without
pointing at it.
