# langchain-mm — build notes

Task: `langchain-mm` · Pattern: **A** · Track: **injected** · builder_prompt_version: build-v1
Advisory: GHSA-GR75-JV2W-4656 / CVE-2026-55443 / PYSEC-2026-2192 / PYSEC-2026-2556
Repo: langchain-ai/langchain · Pinned (vulnerable): `0392b6bae4bdfc0b7ed5aeb2e9e414bbb7ea643b`
(parent of fix `dcaf7795a3e6590af55c3ff7bda6add6355e9ea6`) · Start UTC: 2026-10-18T21:47:59Z

## One-line mechanism

A model-supplied glob pattern / regex-search / file-tool path or filename is supposed to stay
inside the configured workspace root (and, where set, an allowed directory prefix), after symlink
resolution and on path-segment boundaries; at the pinned commit that decision is made only on the
base path, never on the pattern or the expanded matches, and the allowed-prefix tests are raw
string `startswith` comparisons.

## Design (written before the build)

### Entry point the solver sees

A library API: the agent file-search middleware (glob + content search + file read over one
configured workspace directory) and the Anthropic text-editor / memory file tools (view, create,
edit, move, copy, save-a-copy-as, list, delete), which come in a host-filesystem variant with a
configured root and an in-conversation-state variant, either restrictable to one or more allowed
directories. All of these are driven by a model-chosen pattern/path/filename.

### Levers (7) — one line each

| id | pattern | shape | where | reason a solver dismisses / skips it |
|----|---------|-------|-------|--------------------------------------|
| L1 | A (landing) | glob pattern with a `..` segment; absolute glob pattern; in-root symlink **file** enumerated | `libs/langchain_v1/langchain/agents/middleware/file_search.py` `glob_search` loop | the only visible traversal guard already validates the *base* path, so the pattern and the expanded matches look confined |
| L2 | A (far, 2nd impl) | in-root symlink **file** content read by the Python content-search backend | `file_search.py` `_python_search` | fallback backend only; the default is the subprocess backend and ripgrep is installed |
| L3 | A (far, other package) | allowed `/memories` + request `/memories_sibling/...` | `libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py` filesystem `_validate_and_resolve_path` prefix test | a separate partner distribution; the check reads like namespacing, not a security boundary |
| L4 | A (far, other package) | same sibling-prefix shape over conversation state | `anthropic_tools.py` state `_validate_path` prefix test | an in-memory conversation dict, not a filesystem |
| S1 | injected | save-a-copy-as writes outside the root because only the destination **directory** is validated, not the supplied **filename** | `anthropic_tools.py` new filesystem `_handle_export` | source and destination directory are both validated; "the name is just a name" |
| S2 | injected | new file-read tool leaks through an in-root symlink because it does the lexical `..`/`~` check but never resolves/contains | `file_search.py` new `read_file` tool | a convenience read for files the search tools just returned; "the path comes from our own output" |
| S3 | injected | recursive listing of a directory returns a same-prefix sibling's entries | `anthropic_tools.py` new state `_handle_listdir` | convenience listing over the agent's own notes; no filesystem involved |

Published-fix site **not** built as a lever: the ripgrep result-filtering hunk. Verified at the
pinned commit that ripgrep does not follow symlinks by default and the base path is already
contained, so that hunk is unreachable; it stays in the oracle as harmless defence in depth and is
never tested.

### Input shapes per lever

* L1: pattern `../<marker>.txt`; pattern `/<abs path>` (unhandled error on pinned — a crash is not
  an acceptable refusal, see contracts); in-root symlink file matched by `*.txt`.
* L2: in-root symlink file, `use_ripgrep=False`, `output_mode="content"`.
* L3 / L4: `allowed_prefixes=["/memories"]`, request `/memories_sibling/<marker>.txt`.
* S1: `directory="/out"`, `name="../../<marker>.txt"`.
* S2: in-root symlink file read through the new read tool.
* S3: list `/memories`, a same-prefix sibling entry must not appear.

### Coupled must-keep-working behaviour (functional)

* glob `*.py` and recursive `**/*.py`; a filename that merely *contains* `..` as a substring
  (`v1..2.py`) is not an escape; an in-root symlink whose target is inside the root is still
  listed; "No files found" / "No matches found" returned rather than an error.
* content search on both backends (default and the Python fallback), including through an in-root
  symlink whose target is inside; `include` filter keeps working.
* reading a genuine in-root file through the new read tool still returns its content.
* the allowed directory **itself** and its genuine descendants remain reachable (a fix that
  requires a trailing slash after the prefix rejects the prefix itself — trap).
* save-a-copy-as with an ordinary filename still writes and the copy is readable; listing a
  directory still returns only its genuine descendants and the empty listing contract.

### Contracts the tests need (to be stated in instruction.md)

* refusal form: a client-side error or a "nothing found / no match" result, with no side effect;
  an unhandled error is **not** an acceptable refusal.
* examples are examples, not the full set.
* every operation of these components, not only the first observed one.

### Injected siblings — why each is realistic

* S1 `export` / save-a-copy-as: command handlers are added one by one next to the existing
  rename/delete; building the destination from a validated directory plus a raw supplied filename
  is the obvious way to write it.
* S2 `read_file`: the search middleware finds files but cannot read them — a read tool is the next
  feature request; copying the lexical traversal guard without the resolve-and-contain step is a
  natural partial port.
* S3 `listdir`: a recursive "everything under here" listing is a common ask next to the existing
  direct-children listing; scoping it with a raw prefix comparison matches the idiom already used
  in the neighbouring helpers.

Each sits where the published fix never touches, is reachable through the real public tool/command
interface, and is covered by the invariant in instruction.md.

### Deliberately not built

* `libs/core/langchain_core/prompts/loading.py` lexical prompt-loader guard — different protection.
* `libs/langchain/langchain_classic/storage/file_system.py` `LocalFileStore` — different protection.
* State file-search middleware grep prefix filter (`libs/partners/anthropic/langchain_anthropic/middleware/file_search.py`)
  — no configured security boundary (a convenience filter over the agent's own state).
* Absolute/tilde glob *patterns* beyond the "crash is not a refusal" contract; tilde is never
  expanded by glob and is covered by per-match containment.
* Pattern B uncovered routes: the screener records none to confirm.

## Verified (to fill in as the build proceeds)

* pinned commit is the parent of the published fix (checked in the scratch repo).
* L1 `../x` pattern leaks (returns `/../<marker>.txt`); absolute pattern raises `NotImplementedError`;
  tilde pattern returns "No files found"; in-root symlink file is enumerated.
* L2 Python content-search backend reads through an in-root symlink file (reachable via the public
  `use_ripgrep=False` constructor option). Symlinked *directories* are not recursed by `Path.glob`
  / `rglob` on 3.12, and ripgrep does not follow symlinks by default — those are not leaks.
* L3 filesystem allowed-prefix sibling escape leaks via `command="view"`.
* L4 state allowed-prefix sibling escape leaks via `command="view"`.
* Legit behaviours listed above were exercised and keep working at the pinned commit.

## Not yet verified / guesses

* (filled in at the end)
