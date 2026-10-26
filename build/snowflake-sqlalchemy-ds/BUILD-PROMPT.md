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

Project root: `/home/mara/cwe-bench`. Task: `snowflake-sqlalchemy-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-8G6F-QW9X-4Q6Q", "CVE-2026-15736", "PYSEC-2026-3921"]; snowflakedb/snowflake-sqlalchemy; CWE-73 external control of file path via connection-URL parameter injection, bundled with CWE-89 identifier/literal SQL injection in DDL compilers
- Pinned (vulnerable) commit: 20ad218611bad394db55b1e1530e6d4853d2ab6d. Published fix: 2c33792c91449e746a2c7ef24c25f0ede0a4a875, 35edf4dc5e76b9a9fdfa74c8e4f6fd14642110f1, a198ed2197bb3e0be57268032ed6e8b7fdeb8129.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "2121",
 "advisory_ids": [
  "GHSA-8G6F-QW9X-4Q6Q",
  "CVE-2026-15736",
  "PYSEC-2026-3921"
 ],
 "repo": "snowflakedb/snowflake-sqlalchemy",
 "pinned_commit": "20ad218611bad394db55b1e1530e6d4853d2ab6d",
 "fix_commits": [
  "2c33792c91449e746a2c7ef24c25f0ede0a4a875",
  "35edf4dc5e76b9a9fdfa74c8e4f6fd14642110f1",
  "a198ed2197bb3e0be57268032ed6e8b7fdeb8129"
 ],
 "trust_decision": {
  "summary": "Two decisions: (1) which connector kwargs a URL string may set \u2014 create_connect_args forwards every URL query key (including file-path kwargs like token_file_path/private_key_file) to snowflake.connector.connect, and URL() interpolates account/region/user unescaped into the DSN so a field value can add query keys; (2) caller-supplied names/values in custom-command and table-option DDL are emitted without identifier quoting or literal escaping.",
  "evidence": [
   "src/snowflake/sqlalchemy/snowdialect.py:284-285",
   "src/snowflake/sqlalchemy/util.py:57-71",
   "src/snowflake/sqlalchemy/base.py:674",
   "src/snowflake/sqlalchemy/base.py:1104-1107",
   "fix.diff:167-189",
   "fix.diff:229-248"
  ]
 },
 "landing_point": {
  "where": "src/snowflake/sqlalchemy/snowdialect.py:284",
  "why": "The advisory's 'local file disclosure' (CWE-73) half points straight at the loop that copies URL query params into connector kwargs; the 'SQL injection' half leads to the COPY INTO / CREATE STAGE compilers in base.py."
 },
 "fix_sites": [
  {
   "where": "src/snowflake/sqlalchemy/snowdialect.py:284-285",
   "entry_point": "sqlalchemy.create_engine('snowflake://...?<param>=...') -> SnowflakeDialect.create_connect_args",
   "module_kind": "dialect connection-arg translation (core)"
  },
  {
   "where": "src/snowflake/sqlalchemy/util.py:57-71",
   "entry_point": "snowflake.sqlalchemy.URL(account=..., region=..., user=...) (alias of util._url, src/snowflake/sqlalchemy/__init__.py:93)",
   "module_kind": "URL-builder helper (separate util module)"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:484",
   "entry_point": "select(... .label(quoted_name(x, quote=False))) compile -> SnowflakeIdentifierPreparer.format_label",
   "module_kind": "identifier preparer (lower-level API)"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:464-475",
   "entry_point": "Table(schema=quoted_name(x, quote=False)) compile -> quote_schema/_quote_free_identifiers",
   "module_kind": "identifier preparer (lower-level API)"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:584",
   "entry_point": "MergeInto(...).when_not_matched_then_insert().values(**kw) compile",
   "module_kind": "custom command compiler"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:594",
   "entry_point": "MergeInto(...).when_matched_then_update().values(**kw) compile",
   "module_kind": "custom command compiler"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:674",
   "entry_point": "CopyInto(..., formatter=CopyFormatter(format_name=...)) compile",
   "module_kind": "custom command compiler"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:697-766",
   "entry_point": "AWSBucket/AzureContainer/GCSBucket(.from_uri, .credentials, .encryption) used in CopyInto",
   "module_kind": "custom command compiler"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:773",
   "entry_point": "ExternalStage(file_format=...) used in CopyInto",
   "module_kind": "custom command compiler"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:1104-1107",
   "entry_point": "CreateStage(container, stage) DDL compile (used repr(container) as SQL)",
   "module_kind": "DDL compiler / repr used as serializer"
  },
  {
   "where": "src/snowflake/sqlalchemy/base.py:1119",
   "entry_point": "CreateFileFormat(format_name, formatter) DDL compile",
   "module_kind": "DDL compiler"
  },
  {
   "where": "src/snowflake/sqlalchemy/custom_commands.py:107",
   "entry_point": "CopyInto.files([...]) -> FilesOption.__str__",
   "module_kind": "custom command value object (__str__ as serializer)"
  },
  {
   "where": "src/snowflake/sqlalchemy/sql/custom_schema/options/identifier_option.py:52",
   "entry_point": "SnowflakeTable/DynamicTable(warehouse=IdentifierOption(...)) CREATE TABLE compile",
   "module_kind": "table-option renderer (separate package)"
  },
  {
   "where": "src/snowflake/sqlalchemy/sql/custom_schema/options/literal_option.py:56",
   "entry_point": "LiteralOption string value in CREATE TABLE options",
   "module_kind": "table-option renderer (separate package)"
  },
  {
   "where": "src/snowflake/sqlalchemy/sql/custom_schema/options/cluster_by_option.py:49",
   "entry_point": "ClusterByOption(str exprs) in CREATE TABLE",
   "module_kind": "table-option renderer (separate package)"
  },
  {
   "where": "src/snowflake/sqlalchemy/sql/custom_schema/options/as_query_option.py:53",
   "entry_point": "AsQueryOption(select) compiled with default dialect instead of Snowflake dialect",
   "module_kind": "table-option renderer (separate package)"
  }
 ],
 "O1_entry_points": 14,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "src/snowflake/sqlalchemy/util.py:57-71 (URL() helper composes the DSN whose query create_connect_args later trusts); also src/snowflake/sqlalchemy/base.py:1107 (CreateStage used container __repr__, src/snowflake/sqlalchemy/custom_commands.py:535-541, as SQL serializer)"
 },
 "O3_reason_to_dismiss": "Once create_connect_args blocks the sensitive query keys, a solver can argue the URL() builder needs no account/region validation or user encoding because any injected keys are rejected downstream anyway; and repr() is 'debug only' per its docstring (src/snowflake/sqlalchemy/custom_commands.py:125-129) so CREATE STAGE looks like a logging concern.",
 "O4_distance": {
  "files": 7,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Ordinary URL query params (warehouse, role, schema, account, authenticator=externalbrowser, timezone, cache_column_metadata/enable_decfloat) must still be forwarded; blocked params must still work via connect_args= and (fix) a legacy_url_params opt-in. On the DDL side, legal bare identifiers incl. upper-case and quoted_name(quote=False) idiom must stay unquoted, and SA's '__[SCHEMA_<key>]' schema-translate token must pass through quote_schema unchanged.",
  "where": "src/snowflake/sqlalchemy/snowdialect.py:255-285; src/snowflake/sqlalchemy/base.py:470-484; fix.diff:847-898; fix.diff:1841-1851"
 },
 "O6_input_shapes": [
  "sensitive kwarg supplied as a direct URL query key (create_engine string URL / SA URL.create(query=...))",
  "sensitive kwarg smuggled through URL() account field containing ?/&/@/#",
  "same via region field",
  "same via user field (percent-encoded rather than rejected)",
  "dot-qualified identifiers (DB.SCH.NAME) quoted per part",
  "quoted_name(..., quote=False) values that are structurally unsafe",
  "str vs TextClause vs other types in ClusterByOption",
  "int vs str LiteralOption values",
  "single-quote and backslash in literals (Snowflake ESCAPE_STRING_LITERALS)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "src/snowflake/sqlalchemy/util.py:35-92 (URL() DSN serializer feeding create_connect_args at src/snowflake/sqlalchemy/snowdialect.py:227); src/snowflake/sqlalchemy/custom_commands.py:107 (FilesOption.__str__ called via str(v) at src/snowflake/sqlalchemy/base.py:653)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "COPY INTO stage reference: ExternalStage namespace/name/path emitted raw (fix quoted only file_format here, while CREATE STAGE's prefix was quoted)",
   "where": "src/snowflake/sqlalchemy/base.py:771-773",
   "reason_to_dismiss": "Advisory/changelog list 'stage namespaces/names' for CREATE STAGE; a solver can say the @stage path syntax is not an identifier position",
   "distance": "same file as other DDL sites",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "CopyFormatter.value_repr wraps string format options in quotes without escaping (field_delimiter, null_if, date_format, etc.)",
   "where": "src/snowflake/sqlalchemy/custom_commands.py:204-207",
   "reason_to_dismiss": "Formatter option setters look like typed constants; only format_name was in the advisory",
   "distance": "custom_commands.py, separate from base.py compiler",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "COPY INTO from a Table uses copy_into.from_.name unquoted",
   "where": "src/snowflake/sqlalchemy/base.py:614-615",
   "reason_to_dismiss": "Table names are application-defined schema objects, not runtime input",
   "distance": "same function as fixed format_name site",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "copy options PATTERN / STORAGE_INTEGRATION / string partition_by emitted via str(v) raw",
   "where": "src/snowflake/sqlalchemy/base.py:627-628",
   "reason_to_dismiss": "PATTERN takes a caller-quoted regex and partition_by is a documented raw-SQL expression; quoting breaks existing callers",
   "distance": "same function",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "URL() host= branch: host and port interpolated into the DSN authority without validation (fix validated only account/region)",
   "where": "src/snowflake/sqlalchemy/util.py:49-55",
   "reason_to_dismiss": "host is an explicit override the caller is trusted to set; downstream blocklist rejects any query keys it smuggles",
   "distance": "util.py, same function as the fixed account/region branches",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "URL() extra-parameter loop appends dict keys to the query unencoded (values are quote_plus'd)",
   "where": "src/snowflake/sqlalchemy/util.py:86-91",
   "reason_to_dismiss": "Keyword names are code, not data",
   "distance": "same function",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/snowflake/sqlalchemy/snowdialect.py:255-282",
   "sibling": "a second query-param pre-processing path (e.g. a popped dialect-level param whose value is a file path or forwarded into connect kwargs) that bypasses the blocklist loop",
   "why_realistic": "The dialect already pops cache_column_metadata/enable_decfloat/case_sensitive_identifiers from the query before the generic loop; a maintainer adding one more would naturally do it here."
  },
  {
   "where": "src/snowflake/sqlalchemy/snowdialect.py:1701-1709",
   "sibling": "connect() merging extra kwargs (e.g. from an env/config source) into cparams after create_connect_args",
   "why_realistic": "connect() already rewrites cparams (application name); a config-file or env-driven default merge here is a plausible feature and would be a defaults/merge route past the check."
  },
  {
   "where": "src/snowflake/sqlalchemy/util.py:298-318",
   "sibling": "create_snowflake_engine accepting connection params and re-serialising them into the URL query",
   "why_realistic": "This helper already rewrites base_url with urlsplit/urlunsplit; extending it to inject params is a natural convenience."
  }
 ],
 "O9_family": "CWE-73 external control of file path via connection-URL parameter injection, bundled with CWE-89 identifier/literal SQL injection in DDL compilers",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "pip/hatch, SQLAlchemy>=1.4.19, snowflake-connector-python<5 (pyproject.toml:42)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Unit tests compile SQL/call create_connect_args without a server (fix adds tests/test_unit_connections_args.py, tests/test_table_option_quoting.py, tests/test_unit_escaping.py, tests/test_base_quoting.py); many existing tests in tests/test_core.py need a live Snowflake account and must be excluded."
 },
 "O11_fix_minutes": 90,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/snowflake/sqlalchemy/snowdialect.py, src/snowflake/sqlalchemy/util.py, src/snowflake/sqlalchemy/_constants.py, src/snowflake/sqlalchemy/base.py, src/snowflake/sqlalchemy/custom_commands.py, src/snowflake/sqlalchemy/sql/custom_schema/options/{table_option,identifier_option,literal_option,cluster_by_option,as_query_option,keyword_option}.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a denylist check for token_file_path/private_key_file in the create_connect_args loop and stop, leaving URL() field injection, host/protocol, and the DDL quoting sites untouched."
 },
 "out_of_scope_notes": [
  "SnowflakeSecretRedactionFilter change in the fix is formatting-only (fix.diff:119-123).",
  "Whether the snowflake-connector itself validates file-path kwargs was not examined (other repository)."
 ],
 "unverified": [
  "repo_mb not measured (no shell); the src tree looks small, so tiny_repo (<5 MB) may apply \u2014 check before admitting.",
  "Whether other file-path or safety-relaxing connector kwargs (e.g. private_key_file_pwd, insecure_mode, disable_ocsp_checks, proxy_*, oauth URL params) are missing from the blocklist: the connector's DEFAULT_CONFIGURATION is not in the pinned tree.",
  "present_in_latest for all O8 routes: no latest release provided.",
  "The advisory bundles two unrelated mechanisms (URL params and DDL quoting); a task built on it may need to pick one half to keep the report fair.",
  "O1 count is the number of distinct public constructs listed in fix_sites (some sites share one entry point)."
 ]
}
  ```
- Published fix sites:   - src/snowflake/sqlalchemy/snowdialect.py:284-285 — entry point: sqlalchemy.create_engine('snowflake://...?<param>=...') -> SnowflakeDialect.create_connect_args [dialect connection-arg translation (core)]
  - src/snowflake/sqlalchemy/util.py:57-71 — entry point: snowflake.sqlalchemy.URL(account=..., region=..., user=...) (alias of util._url, src/snowflake/sqlalchemy/__init__.py:93) [URL-builder helper (separate util module)]
  - src/snowflake/sqlalchemy/base.py:484 — entry point: select(... .label(quoted_name(x, quote=False))) compile -> SnowflakeIdentifierPreparer.format_label [identifier preparer (lower-level API)]
  - src/snowflake/sqlalchemy/base.py:464-475 — entry point: Table(schema=quoted_name(x, quote=False)) compile -> quote_schema/_quote_free_identifiers [identifier preparer (lower-level API)]
  - src/snowflake/sqlalchemy/base.py:584 — entry point: MergeInto(...).when_not_matched_then_insert().values(**kw) compile [custom command compiler]
  - src/snowflake/sqlalchemy/base.py:594 — entry point: MergeInto(...).when_matched_then_update().values(**kw) compile [custom command compiler]
  - src/snowflake/sqlalchemy/base.py:674 — entry point: CopyInto(..., formatter=CopyFormatter(format_name=...)) compile [custom command compiler]
  - src/snowflake/sqlalchemy/base.py:697-766 — entry point: AWSBucket/AzureContainer/GCSBucket(.from_uri, .credentials, .encryption) used in CopyInto [custom command compiler]
  - src/snowflake/sqlalchemy/base.py:773 — entry point: ExternalStage(file_format=...) used in CopyInto [custom command compiler]
  - src/snowflake/sqlalchemy/base.py:1104-1107 — entry point: CreateStage(container, stage) DDL compile (used repr(container) as SQL) [DDL compiler / repr used as serializer]
  - src/snowflake/sqlalchemy/base.py:1119 — entry point: CreateFileFormat(format_name, formatter) DDL compile [DDL compiler]
  - src/snowflake/sqlalchemy/custom_commands.py:107 — entry point: CopyInto.files([...]) -> FilesOption.__str__ [custom command value object (__str__ as serializer)]
  - src/snowflake/sqlalchemy/sql/custom_schema/options/identifier_option.py:52 — entry point: SnowflakeTable/DynamicTable(warehouse=IdentifierOption(...)) CREATE TABLE compile [table-option renderer (separate package)]
  - src/snowflake/sqlalchemy/sql/custom_schema/options/literal_option.py:56 — entry point: LiteralOption string value in CREATE TABLE options [table-option renderer (separate package)]
  - src/snowflake/sqlalchemy/sql/custom_schema/options/cluster_by_option.py:49 — entry point: ClusterByOption(str exprs) in CREATE TABLE [table-option renderer (separate package)]
  - src/snowflake/sqlalchemy/sql/custom_schema/options/as_query_option.py:53 — entry point: AsQueryOption(select) compiled with default dialect instead of Snowflake dialect [table-option renderer (separate package)]
- Uncovered routes to confirm (pattern B):   - src/snowflake/sqlalchemy/base.py:771-773 — COPY INTO stage reference: ExternalStage namespace/name/path emitted raw (fix quoted only file_format here, while CREATE STAGE's prefix was quoted) (reason to dismiss: Advisory/changelog list 'stage namespaces/names' for CREATE STAGE; a solver can say the @stage path syntax is not an identifier position; still in latest: unknown)
  - src/snowflake/sqlalchemy/custom_commands.py:204-207 — CopyFormatter.value_repr wraps string format options in quotes without escaping (field_delimiter, null_if, date_format, etc.) (reason to dismiss: Formatter option setters look like typed constants; only format_name was in the advisory; still in latest: unknown)
  - src/snowflake/sqlalchemy/base.py:614-615 — COPY INTO from a Table uses copy_into.from_.name unquoted (reason to dismiss: Table names are application-defined schema objects, not runtime input; still in latest: unknown)
  - src/snowflake/sqlalchemy/base.py:627-628 — copy options PATTERN / STORAGE_INTEGRATION / string partition_by emitted via str(v) raw (reason to dismiss: PATTERN takes a caller-quoted regex and partition_by is a documented raw-SQL expression; quoting breaks existing callers; still in latest: unknown)
  - src/snowflake/sqlalchemy/util.py:49-55 — URL() host= branch: host and port interpolated into the DSN authority without validation (fix validated only account/region) (reason to dismiss: host is an explicit override the caller is trusted to set; downstream blocklist rejects any query keys it smuggles; still in latest: unknown)
  - src/snowflake/sqlalchemy/util.py:86-91 — URL() extra-parameter loop appends dict keys to the query unencoded (values are quote_plus'd) (reason to dismiss: Keyword names are code, not data; still in latest: unknown)
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

## Environment (`tasks/snowflake-sqlalchemy-ds/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/snowflake-sqlalchemy-ds/instruction.md`)
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

## Tests (`tasks/snowflake-sqlalchemy-ds/tests/`)
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
- **Wrong-fix patches** go in `build/snowflake-sqlalchemy-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/snowflake-sqlalchemy-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/snowflake-sqlalchemy-ds/manifest.json`:**
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

**Also in `build/snowflake-sqlalchemy-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py snowflake-sqlalchemy-ds --only static
python3 -I builder/gate.py snowflake-sqlalchemy-ds --only nop
python3 -I builder/gate.py snowflake-sqlalchemy-ds --only oracle
python3 -I builder/gate.py snowflake-sqlalchemy-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/snowflake-sqlalchemy-ds/`;
  - edit only `tasks/snowflake-sqlalchemy-ds/`, `build/snowflake-sqlalchemy-ds/` and, for pattern B, the register;
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
