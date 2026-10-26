# snowflake-sqlalchemy-ds — build plan (written before building)

Start (UTC): 2026-10-24T02:56:43Z
Advisory: GHSA-8G6F-QW9X-4Q6Q / CVE-2026-15736 / PYSEC-2026-3921 (snowflakedb/snowflake-sqlalchemy)
Pinned: 20ad218611bad394db55b1e1530e6d4853d2ab6d
Published fix (chain tip): 2c33792c91449e746a2c7ef24c25f0ede0a4a875 (contains 35edf4d, a198ed2, bf7d250)
Pattern: A+B, injected.

## Scope decision
The advisory bundles two unrelated protections: (A) connection-URL parameter injection (CWE-73)
and (B) identifier/literal SQL serialization in the dialect's compilers (CWE-89). This task is
built on half B only. Half A (connection URL / connector kwargs / URL() builder) is left out of
the task; it is noted here and in the final report as outside the built subtask's scope. Reason:
the two halves share no property, and a faithful 45-minute report cannot cover both; the screener
record itself says the task may need to pick one half.

## The one general property (security)
No value supplied by an application may change the structure of a statement the dialect compiles.
A value used as a name is emitted as identifier text, each part quoted when it is not a plain
identifier; a value used as data is emitted as exactly one string literal whose decoded content is
the supplied value. This holds for every value the dialect renders, wherever it reaches the
compiler. The statement must still compile: unsafe values are rendered inert, not refused.
Preservation clause: plain names stay unquoted (including the case the service folds), values that
use the service's escape sequences keep their exact current spelling, values the API accepts as
pre-built SQL expressions pass through unchanged, and output order stays deterministic.

## Levers (main lever first; each has a different reason to dismiss)
L1 [HOW, main] literal-escaping shape + coupled legitimate values.
   shape: a string value with a backslash immediately before a quote; the current code escapes
   quotes only, so Snowflake's ESCAPE_STRING_LITERALS ends the literal early. Coupled: delimiter
   /escape option values that legitimately rely on one backslash (`\n`, `\t`, `\134`) must keep
   their exact spelling; plain values must be unchanged.
   where: custom_commands.py:107 (FilesOption.__str__), custom_commands.py:204-207
   (CopyFormatter.value_repr), base.py:674 / :653 (sinks).
   why dismissed: "the code already escapes quotes; this is handled".
L2 [HOW] identifier quoting honouring `quoted_name(..., quote=False)` without trusting it.
   shape: an application passes a user-derived name already wrapped in quote=False; the preparer
   emits it verbatim. A plausible fix quotes every identifier and breaks the legitimate bare
   idiom; a plausible fix trusts quote=False and leaves the injection. Coupled: legal bare
   identifiers (lowercase aliases, uppercase schema names) stay bare and SQLAlchemy's
   `__[SCHEMA_<key>]` translate token still passes through.
   where: base.py:464-484 (format_label, quote_schema, _quote_free_identifiers); merge keys
   base.py:584/:594; format names base.py:674/:773/:1119.
   why dismissed: "quote=False is an explicit application opt-out".
L3 [A] the table-option package (a separate subsystem) and a subquery compiled with another
   dialect.
   shape: `sql/custom_schema/options` IdentifierOption/LiteralOption/ClusterByOption render raw;
   AsQueryOption compiles its Selectable with the default dialect, so Snowflake's escaping never
   runs on the literal. Coupled: legal option values and TextClause expressions unchanged.
   where: options/identifier_option.py:52, literal_option.py:56, cluster_by_option.py:49,
   as_query_option.py:53.
   why dismissed: "table options are typed developer constants in a different subsystem".
L4 [B, route where the protection never existed] the stage reference in COPY INTO emits its
   namespace/name raw (the published fix quoted only file_format there, and CREATE STAGE's prefix).
   Real, unmodified upstream code at the pinned commit; upstream fixed it later (fcca23c).
   where: base.py:771-773.
   why dismissed: "the @stage path is not an identifier position / the report is about literals".
L5 [HOW] repr()/str() used as the SQL serializer for storage containers.
   shape: CreateStage interpolates repr(container); bucket classes' __repr__ concatenates raw
   credentials and URI. A compiler-level wrap cannot recover the escaping because the producer has
   already lost the boundaries. Coupled: plain containers render byte-identically.
   where: base.py:1104-1107 (visit_create_stage), base.py:697-766 (visit_*_bucket),
   custom_commands.py:535-541, :605-612, :661-666 (__repr__ producers).
   why dismissed: "repr is for debugging, not SQL".
S1 [INJECTED, HOW/where] a second DDL serializer in a separate module: `CreateExternalVolume`
   registered through SQLAlchemy's `compiles` extension point, rendering the volume name, location
   names, URI, credentials, allow-list and comment raw.
   where: new src/snowflake/sqlalchemy/external_volume.py.
   why dismissed: "a separate, newer DDL feature outside the reported compiler paths".
S2 [INJECTED] a new table option in the options package: `TagOption` renders tag names and values
   raw.
   where: new sql/custom_schema/options/tag_option.py, options/__init__.py, table_option.py (TAG key).
   why dismissed: "tags are typed metadata constants".

## Candidate sibling sites / routes found (full list, before picking 2-4)
Real upstream routes (not injected):
 R1 ExternalStage namespace/name/path raw in COPY (base.py:771-773)                -> picked L4
 R2 CopyFormatter.value_repr string options raw (custom_commands.py:204-207)        -> part of L1
 R3 CopyInto from a Table uses .name raw (base.py:614-615)                          -> rejected: table names are application-defined schema objects; very weak entry point
 R4 PATTERN / STORAGE_INTEGRATION / string partition_by raw (base.py:627-628)       -> rejected: documented raw-SQL slots; escaping them breaks the project's own test_copy expectations and the "pre-built SQL expression" preservation clause
 R5 AsQueryOption compiles with the default dialect (options/as_query_option.py:53) -> part of L3 (how-type)
 R6 TargetLagOption.time interpolated into a literal (target_lag_option.py:88)      -> rejected: signature is int, unit is an enum; caller violates the declared type, so a blind fix cannot be expected to cover it fairly
 R7 IdentifierOption.create only accepts str/IdentifierOption                      -> not a route
 R8 KeywordOption renders an enum value                                            -> not a route
 R9 URL host branch / URL extra-parameter keys (util.py)                            -> out of scope (half A)
 R10 connect() / create_connect_args siblings                                       -> out of scope (half A)
Injected sibling candidates (new code):
 C1 CreateExternalVolume + location/credential/allow-list/comment serialization      -> picked S1
 C2 TagOption table option                                                          -> picked S2
 C3 AlterStage reusing repr(container)                                              -> rejected: same storage-container concept as L5; would fall together with it
 C4 MatchByColumnName list value object via the generic copy-options str(v) path     -> rejected: no real Snowflake COPY option takes a column list; unrealistic
 C5 CopyFormatter subclass for a new format with its own value_repr                 -> rejected: same concept as L1, falls together
 C6 CreateStream DDL with raw object names                                          -> rejected: identifier concept already covered by L2/L4; no how-type
 C7 Generic dict-valued table option                                                -> rejected: same concept as S2
Why the picks beat the others: L4 is a route where protection never existed on real upstream code
(strongest recorded shape); S1 is a second serializer in a new module reached by a separate
registration mechanism (compiles) and exercises both identifier and literal positions; S2 lives in
the already-far options package and is a typed-metadata shape. Each pick has a different dismissal
reason and none is a pure spelling/encoding variant.

## Sites/routes/input shapes the security tests cover
- literal sinks: file-name list; free-form format option; storage URI; credential value; comment;
  allow-list; option literal. Shapes: backslash-before-quote, quote+semicolon+marker, plain quote.
- identifier sinks: alias label; schema name; dotted schema; MERGE column keys; format names; stage
  reference name/namespace; table option warehouse; cluster-by expression; tag name; volume and
  location names.
- separate-dialect subquery literal (AsQueryOption with a Selectable).
- every payload carries a marker keyword that must not appear as a bare SQL token, and literal
  payloads must decode back to the supplied value.

## Coupled must-keep-working behaviour (functional tests)
- plain file names/options/stage/credentials/URIs render exactly as today;
- delimiter and escape options keep one backslash (`\n`, `\t`, `\134`) and NULL_IF plain values;
- legal bare identifiers stay bare (lowercase alias, uppercase schema) and the SA schema-translate
  token is untouched; quoted aliases still quoted;
- ClusterByOption TextClause passthrough; plain warehouse/external volume/catalog values;
- project's own compile tests (test_create, test_copy, test_compiler, test_unit_case_sensitivity,
  test_unit_cte, custom_tables compile tests incl. snapshots) pass. `test_copy_into_location` and
  `test_quoted_name_label` need a live engine (deselected); `test_copy_into_storage_csv_extended`
  is deselected because its `NULL_IF=('\N')` expectation pins an escaping choice that a correct
  full-escaping fix may legitimately change (upstream later changed that expectation).

## Known risks / to verify
- bf7d250 (secret logging) is in the published chain but not part of the vulnerability; the oracle
  keeps the source change (harmless, unreferenced by tests). Secret log redaction is not tested.
- A later upstream fix (b8173d2) treats NULL_IF elements as full-escape; this task deliberately
  does not test NULL_IF backslashes, to avoid contradicting the project test that pins `\N`.
- The published fix quotes `quoted_name(..., quote=False)` uppercase labels (BCR change vs pinned);
  the task does not test uppercase labels, only uppercase schemas (which stay bare).
- Need to confirm the verifier image can import the product from /workspace without an editable
  install: ship a .pth + dist-info pointing at /workspace/src.

## Build verification so far (local, no Docker)
- Pinned+injected tree: 34/34 security tests FAIL, 24/24 hidden functional PASS, 150/150 project
  tests PASS (3 deselected: two need a live account; one pins NULL_IF=('\N')).
- Injected+fix.patch tree: 34/34 security PASS, 24/24 hidden functional PASS, 150/150 project PASS.
- environment/injection.patch applied to the pinned checkout reproduces the injected tree;
  solution/fix.patch applied to the injected tree reproduces the oracle tree.
- Every checks/*.patch was applied to a fresh injected tree and run with the same suites:
  miss_l1 4 sec fail; miss_l2 7; miss_l3 5; miss_l4 2; miss_l5 6; miss_s1 7; miss_s2 3;
  published_only 12; crash_as_refusal 18; escape_after_wrap 2; one_direction 1;
  malformed_identity 1; overbroad_quote 8 hidden functional + 54 project functional fail;
  refuse_all 1 hidden + 1 project functional fail; hardening and alternative 0 failures.

## Gate results (UTC)
- static   PASSED 2026-10-24T03:0x  (only the post-build blind patch and FAIRNESS.md are absent, as intended)
- nop      PASSED 2026-10-24T03:14  (all security tests fail on pinned+injected; every functional test passes)
- oracle   PASSED 2026-10-24T03:19  (3 runs, reward 1.0 each, identical results)
- patches  PASSED 2026-10-24T03:4x  (16/16 declared checks behaved: 12 security_fail, 2 functional_fail,
                                   hardening 1.0, alternative 1.0; blind skipped because not written yet)
End (UTC): 2026-10-24T03:43:04Z

## Not verified / guesses
- I did not run either target model (per the brief); whether the two models fail 3/3 is unmeasured here.
- The hidden-suite runner is exercised only through the Docker gate; the local pre-checks used the
  same commands against local installs, not the verifier container.
- CWE-73 half (connection URL / connector kwargs) was not reproduced or tested by this task.
- The connector's full DEFAULT_CONFIGURATION was read (connector 4.8.0) while deciding the scope note;
  no test depends on it.

## Fairness concerns I see myself
- Scope is large (seven rendering areas); an expert could take longer than 45 minutes. Mitigation:
  every property is stated once, every test drives a public API, and the coupled legitimate values are
  exercised by the project's own 150 offline tests.
- The project's `test_copy_into_storage_csv_extended` is deselected because it pins `NULL_IF=('\N')`;
  a correct full-escaping fix may change that SQL spelling. This avoids penalizing a valid fix but
  means that one project expectation is not enforced.
- The published fix quotes an upper-case `quoted_name(..., quote=False)` alias where the pinned code
  left it bare; the hidden suite avoids that BCR corner so a fix that preserves it also passes.
