# snowflake-sqlalchemy-ds — build notes

- Slug: `snowflake-sqlalchemy-ds`
- Pattern: A+B; track: injected
- Advisory: GHSA-8G6F-QW9X-4Q6Q / CVE-2026-15736 / PYSEC-2026-3921 (snowflakedb/snowflake-sqlalchemy)
- Pinned: `20ad218611bad394db55b1e1530e6d4853d2ab6d`
- Published fix commits: `2c33792c91449e746a2c7ef24c25f0ede0a4a875`, `35edf4dc5e76b9a9fdfa74c8e4f6fd14642110f1`,
  `a198ed2197bb3e0be57268032ed6e8b7fdeb8129` (the range also contains `bf7d250`, the copy/stage half).
- Start (UTC): 2026-10-24T02:27:24Z
- End (UTC): _filled at the end_

## Scope choice

The advisory bundles two different protections: (a) CWE-73, connector kwargs / DSN fields injected through
the connection URL, and (b) CWE-89, identifier/literal injection while generating SQL from the dialect's
Python constructs. This task builds **(b) only**. The published connection-URL half is left out of scope
(one line in the report): it is a different property over a different data path, and combining both would
push a fair expert fix well past the time budget. Everything built here is inside the advisory's own
protection, at the pinned commit, in this repository.

## Security property (written once, before the routes)

> Any value an application supplies — including values it derives from data it does not control — that
> the dialect places into generated SQL must be encoded for the position it occupies: an identifier is
> emitted as an identifier, text is emitted as one string literal that keeps its exact value. No such
> value may add, remove or change SQL syntax, clauses, options, statements or identifiers. This holds for
> every public construct the dialect offers for generating a statement, no matter which layer does the
> serialising.

One property, no per-route sentences in the report. The report gives one user-level trigger and says
examples are examples.

Coupled contract (functional): legal names keep today's compiled text exactly (bare names stay bare,
including upper-case names and names passed with the documented no-quote hint); Snowflake's own escape
sequences (a newline delimiter, the `\N` null marker) keep their meaning; integers/keywords/raw-SQL
fragments are untouched; schema-name translation keeps working.

## Levers (each with a different reason a solver would dismiss/skip it)

1. **escape-semantics** — how-type (shape trap). Escaping a value that lands inside a single-quoted
   Snowflake literal must neutralise *backslash-before-quote*, not only double the quote. Sites:
   `custom_commands.py:107` (FILES list), `custom_commands.py:204` (formatter option values),
   `base.py:697-766` (bucket URI/CREDENTIALS/ENCRYPTION), `base.py:1104` (stage container via `repr`),
   `sql/custom_schema/options/literal_option.py:56`.
   Dismissal: doubling the quote looks like the whole job (the old code already did `\'`).
2. **quote-opt-out** — how-type (coupled must-keep-working). An identifier marked "don't quote" is
   emitted verbatim; structurally unsafe values must still be encoded, while legal bare names (incl.
   upper case) and SQLAlchemy's `__[SCHEMA_<key>]` translate token must keep working.
   Sites: `base.py:464-484`. Dismissal: the caller opted out / schema comes from metadata, not input.
3. **nested-compile-dialect** — how-type (separate compilation path the check does not drive).
   `sql/custom_schema/options/as_query_option.py:53` compiles a nested selectable with the *default*
   dialect, so values inside it miss Snowflake's backslash escaping.
   Dismissal: "literal binds are already parameterised; a SELECT compiles itself".
4. **option-identifiers** — where-type, Pattern A second implementation in another package:
   `identifier_option.py:52`, `cluster_by_option.py:49`. Dismissal: "these are config constants".
5. **command-compilers** — where-type, Pattern A far sites in the command compilers:
   `base.py:581/594` (MERGE column keys), `base.py:674/1117/773` (format names), `base.py:1104`
   (stage name). Dismissal: "names are application-defined", "repr is debug-only".
6. **copy-references** — Pattern B, real unmodified upstream code: `base.py:614` (COPY FROM a
   table renders `.name` raw) and `base.py:768-773` (COPY FROM a stage renders namespace/name raw;
   the published fix quoted only its file_format). Dismissal: "table names are schema objects, not
   input"; "the @stage path is not an identifier position".
7. **alter-stage** — injected sibling (S1), a second stage renderer (`AlterStage` command added to
   `custom_commands.py`/`base.py`). Dismissal: "a maintenance command, not the creation path".
8. **tag-option** — injected sibling (S2), a second table-option renderer (`TagOption` added to the
   options package; identifier + literal in one clause). Dismissal: "governance metadata from config".

## Candidate sibling sites/routes found, and picks

Every candidate found before choosing (O8/O8b leads + own search):

| # | candidate | kind | picked? |
|---|---|---|---|
| 1 | COPY INTO from `Table`: `copy_into.from_.name` raw (base.py:614) | real route | **yes — lever 6** |
| 2 | COPY INTO from `ExternalStage`: namespace/name/path raw (base.py:769) | real route | **yes — lever 6** (name/namespace only; path grammar is ambiguous, not tested) |
| 3 | `copy_options` PATTERN / STORAGE_INTEGRATION / string `partition_by` via `str(v)` (base.py:627/648) | real route | no — documented raw-SQL surfaces; quoting breaks callers |
| 4 | `CopyFormatter.value_repr` non-string `str(v)` branch | real route | no — not caller text |
| 5 | `handle_cluster_by` string keys (base.py:1057) | real route | no — verified `denormalize_column_name` already quotes unsafe values |
| 6 | `Table(comment=...)` / column comments | real route | no — verified SQLAlchemy's literal processor + Snowflake `render_literal_value` already escape |
| 7 | `TargetLagOption` time | real | no — integer only |
| 8 | `KeywordOption` value | real | no — closed enum |
| 9 | second query-param pre-processing path (snowdialect) | O8b | no — belongs to the out-of-scope connection half |
| 10 | `connect()` merging env/config kwargs | O8b | no — connection half |
| 11 | `create_snowflake_engine` re-serialising params | O8b | no — connection half |
| 12 | `AlterStage` (second stage renderer) | injected | **yes — lever 7** |
| 13 | `TagOption` (second table-option renderer) | injected | **yes — lever 8** |
| 14 | new formatter subclass overriding `value_repr` | injected | no — contrived (why would a format type escape differently) |
| 15 | new DDL command for warehouses/schemas | injected | no — a whole new command family is implausible for this dialect |
| 16 | merged metadata/dialect defaults feeding options | injected | no — would need a contract name only the sibling uses |

Picks beat the others because they are real code a maintainer would write (12/13), are second
implementations of an operation already guarded elsewhere (12/13), sit far from the reported FILES
sink, and each has a different dismissal (maintenance path / governance metadata / app-defined names /
raw-SQL surface is deliberate / caller opted out of quoting).

## Verified on the pinned copy (behavioural, before relying on it)

Run with the repo's own `.compile(dialect=dialect())` entry points, SQLAlchemy 2.0.36,
snowflake-connector-python 4.8.0:

- FILES list: `x') PURGE = TRUE ...` and `x\') PURGE ...` both break out at pinned; the published fix
  doubles quote + backslash.
- Formatter option value `YYYY') opt --`, `x\''`; NULL_IF tuple element; AWS path / AWS_ROLE credential;
  Azure SAS token; GCS path; CreateStage container: all break out at pinned.
- `quoted_name(..., quote=False)` in a schema / label / table schema: emitted raw at pinned.
- MERGE INSERT/UPDATE column keys raw; `format_name` raw in all three sinks; CREATE STAGE name raw;
  IdentifierOption / ClusterByOption raw; LiteralOption raw; AsQueryOption nested literal keeps a single
  backslash at pinned (default dialect) and is escaped by the oracle.
- COPY INTO from a `Table` named `src) --` and from a stage named `S) --` compile to raw SQL at pinned.
- Injected `AlterStage` and `TagOption` reproduce on the injected pinned tree.
- Coupled behaviour verified unchanged by the oracle: bare/upper-case/dotted quote=False names, the
  `__[SCHEMA_...]` token, `\n` delimiter and `\N` NULL_IF, plain file lists, plain stage/bucket SQL,
  project tests `tests/test_copy.py` / `tests/test_create.py` (run with a no-op schema-init fixture).

## Injected siblings (S1, S2)

- S1 `AlterStage(container, stage)` in `custom_commands.py`, visitor at the end of
  `SnowflakeDDLCompiler` (far from every fix hunk), export in the package `__init__`. Renders
  `ALTER STAGE <ns><name> SET URL=<repr(container)>` exactly like the pinned `CreateStage`.
- S2 `TagOption(tag_name, tag_value)` in `sql/custom_schema/options/tag_option.py`, `TAG` added to
  `TableOptionKey`, exposed through `SnowflakeTable(tag=...)`. Renders `TAG (<name> = '<value>')` raw.
- Both reachable through the real public entry point, covered by the one property, no contract sentence
  of their own; placed where the published fix never touches.

## Out of scope / not built on

- The connection-URL parameter injection half of the advisory (CWE-73) — not tested, not built on.
- Whether the connector itself validates file-path kwargs (other repository).
- Secret redaction / log redaction changes that ship in the same upstream series — unrelated to code
  generation, not part of the property.

## Unverified / guesses

- Exact model behaviour is untested (no trials run here).
- The published fix's `legacy_url_params` shim is not tested (connection half, and the name would have
  to be guessed).
- Server-side acceptance of quoted stage names / paths was not exercised (compile-only task).
