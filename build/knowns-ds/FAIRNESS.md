# Fairness review — knowns-ds

Scope: the 20 authored security tests and 11 authored functional tests. A
targeted scan of every path, identifier and name literal in the pristine project
tests (part of the 203-case functional group) found no legitimate input a
correct guard would reject.

Instruction invariants, quoted once:

- **P1** "No value that names a document, a memory note, a template, a template
  file, or a generated destination may cause the product to read or write a file
  outside the folder it manages for that kind of content. This holds for every
  operation that resolves such a value, whatever the operation is called and
  whatever it returns."
- **P2** "An identifier read back from stored data — a record's own identifier in
  its metadata — is as untrusted as one supplied by a client."
- **P3** "This holds however the value is spelled, including forms another
  platform would treat as a separator, an absolute reference, or an alternate
  file name, and for a symbolic link inside a managed folder whose target is
  outside it."
- **P4** "A value that uses path syntax is not a valid name for an item and must
  be refused, not silently reinterpreted as a name inside the folder."
- **P5** "Refusal must be safe: a client-side error (an error result from the
  assistant tools, a 4xx response from the web API) and no file read, created,
  changed or removed outside the managed folders."
- **K** "Ordinary use must behave exactly as it does today" plus the relevant
  Keep-working bullet.

## 1. Per-test fairness

| # | Test (file::name) | What it asserts | Fair because | Could a correct fix fail it? | Risk |
|---|---|---|---|---|---|
| 1 | sec/mcp::TestSecZZDocReadTraversal | doc get `../secret`, `../secret.md`, `x/../../secret` → tool error, no outside bytes | P1, P3 | no — containment/refusal precedes the read | low |
| 2 | sec/mcp::TestSecZZDocCreateTraversal | create with traversing folder refused; no external file | P1 ("write"), P4 | no | low |
| 3 | sec/mcp::TestSecZZDocRenameTraversal | rename to traversing newPath refused; no external file; original still readable | P1, P4, P5 | no | low |
| 4 | sec/mcp::TestSecZZDocDeleteTraversal | delete `../secret` refused; outside file survives | P1 ("removed"), P4 | no (weak test: the read guard already stops the handler) | low |
| 5 | sec/mcp::TestSecZZDocImportLookupTraversal | get `../secret` refused; no imported-file leak | P1 (document name, every operation) | no (local guard refuses first — see §2) | low |
| 6 | sec/mcp::TestSecZZDocSymlinkEscape | symlink inside docs to outside target refused, no leak | P3 ("symbolic link inside a managed folder") | no | low |
| 7 | sec/mcp::TestSecZZMemoryReadTraversal | memory get with slash-bearing id refused, no leak | P1 (memory note), P3 | no | low |
| 8 | sec/mcp::TestSecZZMemoryCreateTraversal | review-create with traversing id refused; no external file | P1, P4 | no | low |
| 9 | sec/mcp::TestSecZZMemoryDeleteTraversal | delete with traversing id refused; outside file survives | P1, P4 | no | low |
| 10 | sec/mcp::TestSecZZMemoryIdentifierShapes | `zzbad.`, `zzbad\route`, `zzbad:stream` refused; no `zzbad` file written | P3 ("separator", "alternate file name"), P4; K's identifier chars | no — an identifier allowlist refuses all three; thinnest wording (see Human review) | medium |
| 11 | sec/mcp::TestSecZZMemoryPromoteStoredIdentifier | promote of a record whose frontmatter id traverses refused; no external file; original intact | P2, P5 | no | low |
| 12 | sec/mcp::TestSecZZMemorySnapshotTraversal | snapshot read with traversing id refused, no leak | P1 ("every operation ... whatever it returns") | no | low |
| 13 | sec/mcp::TestSecZZTemplateCreateTraversal | template create with traversal refused; no external dir/file | P1 (template), P4 | no | low |
| 14 | sec/mcp::TestSecZZTemplateImportTraversal | import-qualified name with traversing tail refused, no leak | P1; K (slash by design) | no | low |
| 15 | sec/mcp::TestSecZZDocIdentifierShapes | absolute, backslash, volume, UNC, device spellings refused; no `zz-knowns` file | P3, P4 | no | low |
| 16 | sec/routes::TestSecZZDocRouteReadTraversal | GET plain and URL-encoded traversals → 4xx, no leak | P1, P5 | no — P5 fixes the 4xx form | low |
| 17 | sec/routes::TestSecZZPreviewFileTraversal | preview `templateFile` traversal → 4xx, no leak | P1 ("a template file"), P5 | no | low |
| 18 | sec/routes::TestSecZZPreviewDestinationTraversal | variable-substituted action destination outside project → 4xx, no leak | P1 ("a generated destination"), P5 | no | low |
| 19 | sec/routes::TestSecZZDocSourceTraversal | raw-source wildcard traversal → 4xx, no leak | P1 ("whatever the operation is called and whatever it returns") | no | low |
| 20 | sec/routes::TestSecZZMemoryPromoteStoredIdentifierRoute | HTTP promote with stored traversing id → 4xx; no external file; original intact | P2, P5 | no | low |
| 21 | func/mcp::TestFuncZZDocNestedLifecycle | nested CRUD, `.md` suffix, `guides/v1..2` name | K (nested, suffix, dots) | no — containment allows `v1..2` | low |
| 22 | func/mcp::TestFuncZZDocImportedShortReference | imported doc by `patterns/foo` and `src/patterns/foo` | K (imported full/short reference) | no | low |
| 23 | func/mcp::TestFuncZZMemoryLifecycleWithDottedID | dotted id CRUD, promote to global, demote to project | K (charset, promote/demote) | no | low |
| 24 | func/mcp::TestFuncZZMemoryTitleSlugReference | title-slug reference resolves to the entry | K (title slug) | no | low |
| 25 | func/mcp::TestFuncZZMemorySnapshotContent | snapshot returns the pre-update copy | "Ordinary use ... exactly as it does today" (examples not exhaustive) | no | low |
| 26 | func/mcp::TestFuncZZTemplateLocalAndImported | dotted local template create/get/run; import-qualified get | K (local name, import-qualified slash) | no | low |
| 27 | func/routes::TestFuncZZDocRouteReadUpdateSource | route read/update/history and raw source keep working | K; "Every response field ... keeps its name and meaning" | no — a fix must keep the raw read | low |
| 28 | func/routes::TestFuncZZDocRouteRenameDottedFolder | rename to `guides/v9..10/setup` works | K (dots, rename) | no | low |
| 29 | func/routes::TestFuncZZPreviewDestinationContent | in-project destination and its current contents returned | K; "Every response field ..." | no | low |
| 30 | func/routes::TestFuncZZPreviewRendersVariables | preview renders variables and `world.ts` | "Ordinary use ... today" | no | low |
| 31 | func/routes::TestFuncZZMemoryRoutePromoteDemote | HTTP promote/demote still work | K (promote/demote) | no | low |

## 2. Leniency (quality, non-blocking)

| Property/trap | Most plausible wrong fix | Caught? |
|---|---|---|
| P1 | Guard only `DocStore.Get` (the reported read) | yes — DocCreate/DocRename/TemplateCreate/TemplateImport/PreviewFile/PreviewDestination/DocSource tests; `sf-miss-doc-writes`, `sf-miss-templates`, `sf-miss-preview-destination`, `sf-miss-doc-source` |
| P1 | Reject any path containing `..` (overbroad) | yes — TestFuncZZDocNestedLifecycle, TestFuncZZDocRouteRenameDottedFolder; `ff-overbroad` |
| P1 | Handler-level guards for MCP and the tested routes only | partly — HTTP `PUT /docs/*` writes and HTTP memory get/update/delete are untested; a handler-only fix passes |
| P2 | Validate only client-supplied ids | yes — TestSecZZMemoryPromoteStoredIdentifier and its Route variant; `sf-miss-memory-stored` |
| P3 | Reject `..` and a leading `/` only | yes — TestSecZZDocSymlinkEscape, TestSecZZDocIdentifierShapes, TestSecZZMemoryIdentifierShapes; `sf-miss-doc-shapes` |
| P4 | Normalise backslash/absolute into the root instead of refusing | mostly — memory shapes and doc create shapes catch it; a leading-`/` **read** is untested (the blind fix retains `TrimPrefix(path,"/")` in `Get`) |
| P5 | Return 500/plain success, or mutate before validating | yes — route tests require 4xx, MCP tests require IsError, promote/rename tests require no side effects |
| T1 | "Report is about docs and memory; templates are another feature" | yes — TemplateCreate, TemplateImport, PreviewFile; `sf-miss-templates` |
| T2 | "The observed impact is a read; writes share the store" | yes — DocCreate, DocRename, DocDelete, DocIdentifierShapes; `sf-miss-doc-writes` |
| T3 | Plain `..` check, no symlink/platform handling | yes — DocSymlinkEscape, DocIdentifierShapes, encoded route read; `sf-miss-doc-shapes` |
| T4 | "Memory ids are generated tokens, so no check is needed" | yes — MemoryRead, MemoryCreate, MemoryDelete, MemoryIdentifierShapes; `sf-miss-memory-request` |
| T5 | "The id came from our own file, so it is trusted" | yes — MemoryPromoteStoredIdentifier (both layers); `sf-miss-memory-stored` |
| S1 | "Snapshot is internal bookkeeping" | yes — TestSecZZMemorySnapshotTraversal; `sf-miss-memory-snapshot` |
| S2 | "Destination is template-author configuration" | yes — TestSecZZPreviewDestinationTraversal; `sf-miss-preview-destination` |
| S3 | "Export is the same store read" | yes — TestSecZZDocSourceTraversal; `sf-miss-doc-source` |

Wrong fixes no test catches: (a) a handler-only fix that guards the MCP tools
and the tested routes but leaves HTTP `PUT /docs/*` rename/update open; (b) an
absolute or volume spelling on a document **read** — only create is driven with
those shapes; (c) HTTP memory get/update/delete traversal — only promote is
tested; (d) a direct `DocStore.Delete("../x")` — the handler fetches first, so
the delete test cannot isolate the delete guard (the build notes admit this);
(e) TestSecZZDocImportLookupTraversal never reaches the import branch, because
the local path guard refuses `../secret` first.

## 3. Hints (quality, non-blocking)

- "A local web API request for the document named `../notes` returns the
  contents of `notes.md`" — the example is a legitimate reproduction, but the
  channel word points at an entry point. Neutral: "A request returns the
  contents of a file outside the library."
- "The same kind of value also lets a client write, rename or delete files
  outside the library, read or remove memory notes outside the memory folders,
  and reach files outside the template library." — enumerates T1/T2/T4. Neutral:
  "The same kind of value affects other operations and other kinds of content."
- "Documents can be created, read, updated, renamed, deleted, previewed and
  exported; notes can be ... promoting or demoting them; templates ... their
  files are previewed" — a route/operation checklist. Neutral: "The product
  creates, reads, updates, moves and deletes several kinds of content."
- "An identifier read back from stored data — a record's own identifier in its
  metadata" — names T5's mechanism. Neutral: "No value is trusted because of
  where it came from."
- "including forms another platform would treat as a separator, an absolute
  reference, or an alternate file name, and for a symbolic link" — a variant
  list naming T3. Neutral: "including every spelling or indirection that could
  denote another file."
- "A value that uses path syntax is not a valid name ... must be refused, not
  silently reinterpreted" — states the fix approach. Neutral: "A value that is
  not a plain item name is invalid and is rejected."
- The Keep-working literals `guides/setup`, `v1..2`, `source/name` are exact test
  inputs and hand the overbroad-check discriminator to the solver. Neutral:
  "Ordinary names, including names containing dots, nested paths, both memory
  scopes, local and imported template names and imported-document references,
  keep working."

## 3a. Required: generalize

1. "Documents can be created, read, updated, renamed, deleted, previewed and
   exported; notes can be ... promoting or demoting them; templates are selected
   by name and their files are previewed before generation." → "The product
   manages several kinds of content through several operations; each kind has a
   folder it manages."
2. "The same kind of value also lets a client write, rename or delete files
   outside the library, read or remove memory notes outside the memory folders,
   and reach files outside the template library." → "The same kind of value
   affects other operations and other kinds of content."
3. P1's list "a document, a memory note, a template, a template file, or a
   generated destination" → "any item the product stores, references or
   generates". State containment once over the managed folders.
4. P2's "a record's own identifier in its metadata" → "any identifier the
   product reads back from its own stored data".
5. P3's "a separator, an absolute reference, or an alternate file name, and ...
   a symbolic link" → "every spelling or indirection by which a resolved path
   could denote a file outside the managed folder".
6. The Keep-working bullet literals (`guides/setup`, `v1..2`, `source/name`,
   promote/demote) → "ordinary names, nested references and existing identifier
   forms keep working".
7. Entry-point/product words "command line tool", "assistant-facing tool
   server", "web UI", "web API", and "Memory notes can also live in a
   machine-level folder shared across projects" → "the product's interfaces" and
   "notes may be held at more than one scope" (the refusal rule may keep naming
   the tool-error and 4xx forms, as those are the tested outcomes).

## 4. Realism

T1–T5 are published-fix sites and are realistic by definition. S1 mirrors the
memory store's existing filename/helper style and is reachable through the real
memory tool; S2 is a natural "show the current destination so the UI can diff"
addition in the same preview handler; S3 follows the document routes' existing
wildcard-suffix dispatch (history/diff/restore) and is reachable via
`GET /docs/*/source`. None looks planted; no flags.

## Verdict

**GATE_A: READY.** Every authored test asserts an outcome that follows from P1
(every operation and item kind, including the source, snapshot and preview
sibling routes), P2 (stored identifier), P3 (spellings and symlinks) or P5/P4
(refusal form). The reference fix, the pass-alt fix and the independently
written `checks/blind.patch` all satisfy the suite; no test demands an error
class beyond the stated tool-error/4xx. The only judgment is
TestSecZZMemoryIdentifierShapes' trailing-dot and colon cases: P3's "alternate
file name" clause plus standard NTFS naming knowledge (trailing dots collapse
and a colon starts an alternate data stream) makes refusal derivable, and the
blind fix's `ValidateMemoryID` rejects both.

**Required: generalize** — see §3a, items 1–7: replace the operation checklist,
the sibling enumeration, the object-kind list, the metadata mechanism, the
spelling/symlink variant list, the exact Keep-working literals and the
entry-point words with the single containment property stated over the managed
folders.

**Quality to tighten** — add security cases for HTTP `PUT /docs/*` writes and
HTTP memory get/update/delete; add an absolute/volume spelling to a document
**read**; make the import-lookup test reach the import branch or drop it; assert
the original body survives a refused rename; add a direct store-level delete
case; neutralise the §3 hint wording.

**Human review:** confirm that P3's "alternate file name" is intended to require
refusing trailing-dot and colon (NTFS ADS) memory ids; if not,
TestSecZZMemoryIdentifierShapes' trailing-dot and colon subtests demand a
refusal not derivable from the instruction.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
