# Pre-trial fairness and leniency review — `prompty-path-read-inj`

Scope: `tasks/prompty-path-read-inj/instruction.md`, all files under
`tasks/prompty-path-read-inj/tests/`, `solution/fix.patch`,
`build/prompty-path-read-inj/manifest.json`, `notes.md` and `checks/*.patch`.
Nothing was executed; no upstream material was consulted. The shipped `/app`
tree is not present in this checkout, so realism judgments about source code are
made from the patches, tests, notes and manifest.

Instruction text is referenced as **I-P1** (first security bullet), **I-P2**
(second security bullet), **I-KW** ("Keep working") and **I-C** ("Constraints").

- I-P1: "No path expressed in a prompt document may cause loading that document
  to read a file outside the directory that contains the document. This holds
  for every way a document can name an external target — injected file contents,
  an included text fragment, an inherited base document, and a referenced child
  prompt — and regardless of how the path is spelled (a relative path that walks
  upward, an absolute path, or a link that points outward)."
- I-P2: "When a path would escape the prompt's directory, loading fails with a
  client-side error and no such file is opened or read. Partial reads, or
  returning the out-of-directory contents, are not acceptable."

---

## 1. Test-by-test fairness

### 1a. Hidden security tests (`tests/security/test_file_reference_containment.py`)

All six use `_assert_blocked`: any exception from `call()` counts as a clean
refusal; otherwise the random token must not appear in `_blob(agent)`
(description, instructions, repr of inputs/metadata/model/sample).

| test (file::name) | what it asserts | instruction basis | correct fix could fail? | risk |
|---|---|---|---|---|
| `security/test_file_reference_containment.py::test_frontmatter_file_relative_traversal` | Load a prompt whose `description` is `${file:../secret.txt}`; the token outside the prompt dir must not reach the loaded object. | I-P1: "injected file contents" + "a relative path that walks upward"; I-P2. | **no** — any containment of the file sink rejects it. | low |
| `security/test_file_reference_containment.py::test_frontmatter_file_absolute_path` | Same, with an absolute `/tmp/.../secret.txt` in `${file:}`. | I-P1: "an absolute path". | **no** — exact string match to the stated invariant. | low |
| `security/test_file_reference_containment.py::test_frontmatter_file_symlink_escape` | A symlink inside the prompt dir points to the outside secret; `${file:link.txt}` must not leak it. | I-P1: "a link that points outward". | **no** — requires resolving symlinks, which the instruction names. Note the test calls `pytest.skip` if symlink creation fails and `score.py` counts a skip as failure (line 34); on a filesystem without symlinks every correct fix scores 0. Not the normal Docker case, but an environment assumption to keep. | low |
| `security/test_file_reference_containment.py::test_frontmatter_prompt_fragment_traversal` | `${prompt:../secret.md}` must not inline the outside token. | I-P1: "an included text fragment". | **no** | low |
| `security/test_file_reference_containment.py::test_base_template_traversal` | `base: ../base.prompty` must not inherit the outside token. | I-P1: "an inherited base document". | **no** | low |
| `security/test_file_reference_containment.py::test_prompty_tool_child_path_traversal` | A parent with `tools: [{kind: prompty, path: ../secret.prompty}]`; after the test itself calls `prompty.load(parent)` and takes `agent.tools[0]`, `_project_prompty_tool` must not surface the outside token. | I-P1: "a referenced child prompt"; I-P2: "loading fails with a client-side error". | **maybe / yes (see gate a)** — the test performs `agent = prompty.load(parent)` and `tool = agent.tools[0]` **outside** `_assert_blocked`'s try/except. A correct fix that validates child-prompt paths eagerly while loading the document (a fail-closed design directly supported by "the loader reads it relative to the prompt file's own directory" and by I-P2's "loading fails") raises in `prompty.load`, so the test errors before `call()` is reached. The instruction nowhere says the refusal must surface only at wire projection. | **high** |

### 1b. Hidden functional tests (`tests/functional/test_reference_legitimate_use.py`)

| test (file::name) | what it asserts | instruction basis | correct fix could fail? | risk |
|---|---|---|---|---|
| `functional/test_reference_legitimate_use.py::test_file_reference_in_prompt_dir_returns_structured_data` | `${file:shared_connection.json}` beside the prompt is parsed as structured data used as `model.connection` (kind/endpoint). | I-KW: "a structured reference (JSON or YAML) that must still be returned as parsed, structured data — not flattened to text or dropped". | **no** — oracle and both pass-patches keep this. | low |
| `functional/test_reference_legitimate_use.py::test_file_reference_in_subdirectory_works` | `${file:frags/desc.txt}` resolves into a sub-directory. | I-KW: "a reference into a sub-directory of the prompt's directory". | **no** | low |
| `functional/test_reference_legitimate_use.py::test_prompt_fragment_in_prompt_dir_inlined` | `${prompt:frag.md}` beside the prompt is inlined as text. | I-KW: "an included text fragment ... whose target lives inside the prompt's directory". | **no** | low |
| `functional/test_reference_legitimate_use.py::test_base_template_in_prompt_dir_inherited` | `base: base.prompty` in the prompt dir contributes `description`. | I-KW: "an inherited base document ... whose target lives inside the prompt's directory". | **no** | low |
| `functional/test_reference_legitimate_use.py::test_prompty_tool_child_in_prompt_dir_projects` | A `kind: prompty` tool with `path: child.prompty` in the prompt dir projects with the child's description. | I-KW: "a child-prompt tool whose target lives inside the prompt's directory". | **no** | low |

### 1c. Project suite (pristine upstream copies run by `tests/test.sh`)

Basis **B** = standard expert knowledge: the project's own visible suite defines
the "keep working" contract, and the instruction says "Keep every legitimate use
working" and "Do not modify or add tests". All references in the shipped fixture
`prompts/` stay inside that directory (`shared_connection.json`, `schema.json`,
`weather_spec.json`, `./summarize_child.prompty`), so containment does not alter
any of them. `test_loader.py`'s `test_load_file_not_found_raises` writes a
temporary prompt inside `prompts/` and expects `FileNotFoundError` "not found"
for an in-dir missing target; containment preserves that path.

`functional/project/test_loader.py`:

| test | asserts | basis | fail? | risk |
|---|---|---|---|---|
| `TestBasicLoading::test_load_basic` | basic prompt loads with name/description under env vars | B | no | low |
| `TestBasicLoading::test_load_minimal` | name and `model.id` | B | no | low |
| `TestBasicLoading::test_load_returns_prompt_agent` | returns `Prompty` | B | no | low |
| `TestBasicLoading::test_load_kind_is_prompt` | returns `Prompty` | B | no | low |
| `TestBasicLoading::test_load_missing_file` | missing prompt raises `FileNotFoundError` | B | no | low |
| `TestBasicLoading::test_load_no_model` | prompt without model gets default model | B | no | low |
| `TestInstructions::test_load_instructions_from_body` | body becomes instructions | B | no | low |
| `TestInstructions::test_load_instructions_roles` | role markers preserved | B | no | low |
| `TestInstructions::test_load_thread_input_kind` | thread input parsed | B | no | low |
| `TestModel::test_load_model_id` | `model.id` | B | no | low |
| `TestModel::test_load_model_full` | provider/apiType | B | no | low |
| `TestModel::test_load_model_connection` | `ApiKeyConnection` from env | B | no | low |
| `TestModel::test_load_model_options` | temperature/token options | B | no | low |
| `TestSchema::test_load_input_schema` | three input names | B | no | low |
| `TestSchema::test_load_input_values` | input kind | B | no | low |
| `TestTools::test_load_tools_function` | function tool and parameters | B | no | low |
| `TestTools::test_load_tools_function_params` | parameter names | B | no | low |
| `TestTools::test_load_tools_mcp` | MCP tool/connection | B | no | low |
| `TestTools::test_load_tools_openapi` | OpenAPI tool/connection | B | no | low |
| `TestTools::test_load_tools_custom` | unknown kind becomes `CustomTool` | B | no | low |
| `TestTemplate::test_load_template` | jinja2/prompty template | B | no | low |
| `TestMetadata::test_load_metadata` | metadata preserved | B | no | low |
| `TestReferenceResolution::test_load_env_resolution` | `${env:}` resolves | B | no | low |
| `TestReferenceResolution::test_load_env_default` | `${env:VAR:default}` fallback | B | no | low |
| `TestReferenceResolution::test_load_env_missing_raises` | missing env raises `ValueError` "not set" | B | no | low |
| `TestReferenceResolution::test_load_file_resolution` | `${file:schema.json}` in-dir loads | B + I-KW structured file reference | no | low |
| `TestReferenceResolution::test_load_file_not_found_raises` | in-dir missing `${file:}` raises `FileNotFoundError` "not found" | B | no — oracle's `exists()` branch preserves the message | low |
| `TestFileSharedConfig::test_load_shared_connection` | in-dir shared JSON connection | B + I-KW | no | low |
| `TestFileSharedConfig::test_load_shared_connection_kind` | connection kind | B + I-KW | no | low |
| `TestShorthand::test_model_string` | shorthand model string | B | no | low |
| `TestShorthand::test_empty_frontmatter` | empty frontmatter loads | B | no | low |
| `TestShorthand::test_body_only` | body-only file loads | B | no | low |
| `TestShorthand::test_quick_prompt` | compact prompt/inputs | B | no | low |
| `TestShorthand::test_no_name` | default empty name | B | no | low |
| `TestShorthand::test_name_only` | name-only prompt | B | no | low |
| `TestShorthand::test_shorthand_threaded` | thread input in shorthand | B | no | low |
| `TestAsyncLoading::test_load_async_basic` | async load works | B | no | low |
| `TestAsyncLoading::test_load_async_missing_file` | async missing file raises | B | no | low |

`functional/project/test_tool_dispatch.py`:

| test | asserts | basis | fail? | risk |
|---|---|---|---|---|
| `TestNameRegistry::test_register_and_get` | name registry round-trip | B | no | low |
| `TestNameRegistry::test_get_missing_returns_none` | missing name is `None` | B | no | low |
| `TestNameRegistry::test_clear_removes_all` | clear registry | B | no | low |
| `TestNameRegistry::test_overwrite` | last registration wins | B | no | low |
| `TestKindHandlerRegistry::test_builtin_handlers_registered` | built-in handlers present | B | no | low |
| `TestKindHandlerRegistry::test_get_missing_raises` | unknown kind raises | B | no | low |
| `TestKindHandlerRegistry::test_clear_and_reregister` | clear/re-register | B | no | low |
| `TestKindHandlerRegistry::test_custom_handler` | custom handler dispatch | B | no | low |
| `TestDispatchPriority::test_user_tools_wins_over_name_registry` | dispatch priority | B | no | low |
| `TestDispatchPriority::test_name_registry_wins_over_kind_handler` | dispatch priority | B | no | low |
| `TestDispatchPriority::test_kind_handler_fallback` | kind handler fallback (mocked) | B | no | low |
| `TestDispatchPriority::test_nothing_found_returns_error` | error string | B | no | low |
| `TestDispatchTool::test_invalid_json` | invalid JSON error | B | no | low |
| `TestDispatchTool::test_empty_arguments` | empty args accepted | B | no | low |
| `TestDispatchTool::test_user_tool_error_caught` | user error string | B | no | low |
| `TestDispatchTool::test_async_fn_in_sync_dispatch_errors` | async-in-sync error | B | no | low |
| `TestDispatchToolAsync::test_async_user_tool` | async user tool | B | no | low |
| `TestDispatchToolAsync::test_sync_fn_works_in_async_dispatch` | sync in async | B | no | low |
| `TestDispatchToolAsync::test_async_name_registry` | async registry | B | no | low |
| `TestFunctionToolHandler::test_sync_raises` | no callable raises | B | no | low |
| `TestFunctionToolHandler::test_dispatch_to_function_kind_without_callable` | error string | B | no | low |
| `TestPromptyToolHandler::test_resolve_child_path` | `_resolve_child_path` returns `str(PROMPTS_DIR / "summarize_child.prompty")` | B; instruction "Keep every legitimate use working" | no in practice — the oracle returns the resolved path as `str`. A fix that changed the return type to `Path` would fail, but that is a gratuitous breaking change of a method the repo's own suite exercises. | low |
| `TestPromptyToolHandler::test_missing_source_path_raises` | no `__source_path` raises | B | no | low |
| `TestPromptyToolHandler::test_execute_tool_loads_and_runs` | loads child and runs pipeline (mocked) | B + I-KW in-dir child tool | no | low |
| `TestPromptyToolHandler::test_execute_tool_error_returns_string` | load error becomes string | B | no — in-dir missing child still fails inside the try | low |
| `TestPromptyToolHandler::test_circular_reference_detected` | circular chain caught | B | no | low |
| `TestPromptyToolHandler::test_circular_self_reference` | self reference caught | B | no | low |
| `TestPlaceholderHandlers::test_mcp_sync` | MCP not implemented | B | no | low |
| `TestPlaceholderHandlers::test_openapi_sync` | OpenAPI not implemented | B | no | low |
| `TestPlaceholderHandlers::test_custom_sync` | custom not implemented | B | no | low |
| `TestPlaceholderHandlers::test_mcp_async` | MCP async not implemented | B | no | low |
| `TestPlaceholderHandlers::test_openapi_async` | OpenAPI async not implemented | B | no | low |
| `TestPlaceholderHandlers::test_custom_async` | custom async not implemented | B | no | low |
| `TestWireProjection::test_project_prompty_tool` | in-dir tool parses | B | no | low |
| `TestWireProjection::test_wire_format` | wire function def/params/bindings | B + I-KW in-dir child tool | no | low |
| `TestWireProjection::test_wire_format_through_tools_to_wire` | end-to-end wire list | B + I-KW | no | low |
| `TestWireProjection::test_missing_source_path_raises` | missing `__source_path` raises | B | no | low |
| `TestWireProjection::test_missing_tool_path_raises` | empty tool path raises "has no path" | B | no | low |
| `TestWireProjection::test_child_with_no_inputs_emits_empty_schema` | empty parameter schema (mocked child) | B | no | low |

---

## 2. Leniency (quality, non-blocking)

### Security properties

**P1 — no out-of-directory read through any of the four sinks, any spelling.**

| most plausible wrong fix | caught? |
|---|---|
| Reject only references containing `..` (`checks/sf-dotdot-only.patch`) | **Yes.** `test_frontmatter_file_absolute_path` (absolute path has no `..` and still resolves to the secret) and `test_frontmatter_file_symlink_escape` (symlink name has no `..`; `.resolve()` follows it out). |
| Lexical `normpath`/`startswith` containment without symlink resolution | **Yes**, by `test_frontmatter_file_symlink_escape`. |
| Fix only the `${file:}` branch (`checks/sf-file-only.patch`) | **Yes**, by `test_frontmatter_prompt_fragment_traversal` and `test_base_template_traversal`. |
| Fix only `loader.py` sinks (`checks/sf-loader-only.patch`) | **Yes**, by `test_prompty_tool_child_path_traversal`. |
| Guard only `_project_prompty_tool` (`executor.py:155`) and leave `PromptyToolHandler._resolve_child_path` (`tool_dispatch.py:277`) unguarded — the sibling route the oracle does patch | **No.** No security test drives `dispatch_tool`/`execute_tool` with an out-of-directory child path; the project test uses an in-dir child. A grader-passing fix can leave the tool-execution read open. |
| Silently drop/ignore an escaping reference instead of failing | **No.** `_assert_blocked` accepts a returned object that lacks the token (lines 38–48), so dropping passes even though I-P2 requires "loading fails with a client-side error". |
| Read the file first, then validate and raise | **No.** `_assert_blocked` treats any exception as "refused before reading"; no test observes an open/read. Violates I-P2's "no such file is opened or read. Partial reads ... are not acceptable." |

**P2 — client error, no read/partial read.** Covered in the table above: the
harness is deliberately non-specific about the exception type (good), but it
also cannot distinguish "refused before opening" from "opened, read, then
raised", and accepts a silent no-op instead of an error.

### Traps (manifest.traps)

- **T1 — frontmatter `${file:}` (loader.py:164).** Wrong fix: `..`-string-only
  rejection (most plausible; `sf-dotdot-only.patch`). Caught by
  `test_frontmatter_file_absolute_path` and
  `test_frontmatter_file_symlink_escape`. The instruction's parenthetical
  ("a relative path that walks upward, an absolute path, or a link that points
  outward") defuses this lever by naming all three shapes, but the tests do
  catch the wrong fix.
- **T2 — PromptyTool child path via wire projection (executor.py:155).** Wrong
  fix: patch only the loader (`sf-loader-only.patch`). Caught by
  `test_prompty_tool_child_path_traversal`. Wrong fix: patch only the dispatch
  route (`tool_dispatch.py`) and not the projection — also caught by the same
  test. Wrong fix: patch only the projection and not the dispatch route —
  **not caught** (see P1 row 5).
- **T3 — `${prompt:}` fragment (loader.py:172 → `utils.load_fragment`).** Wrong
  fix: patch only `${file:}` (`sf-file-only.patch`). Caught by
  `test_frontmatter_prompt_fragment_traversal`.
- **T4 — base-template include (loader.py:100).** Wrong fix: same
  `sf-file-only.patch`; caught by `test_base_template_traversal`. Note
  `sf-file-only` fails both T3 and T4, so it cannot distinguish which sibling
  was missed.

Over-hardening is covered: `ff-refuse-all.patch` (all legitimate references
refused) fails the five model-usage functional tests in
`test_reference_legitimate_use.py`, and `score.py` forces reward 0 on any
functional failure.

### Wrong fixes no test catches

1. Guarding `_project_prompty_tool` only; `PromptyToolHandler._resolve_child_path`
   still joins and loads an arbitrary child path.
2. Silent drop of escaping references (no client error).
3. Read-then-refuse: opening/reading the target before the containment check
   raises.
4. (Minor) Fixing only relative/absolute traversal but not symlinks is caught;
   fixing only symlink-realpath on the final component while the prompt
   directory itself is reached through a link is not exercised — low value.

---

## 3. Hints (quality, non-blocking)

1. **Input-shape enumeration (T1 lever).** "regardless of how the path is
   spelled (a relative path that walks upward, an absolute path, or a link that
   points outward)" names exactly the three spellings the hidden tests use.
   Neutral wording: "regardless of how the path is spelled". (Absolute and
   symlink escape are standard expert knowledge for containment.)
2. **Sink enumeration (T2–T4).** "This holds for every way a document can name
   an external target — injected file contents, an included text fragment, an
   inherited base document, and a referenced child prompt" is a one-to-one list
   of the four levers. Proposed neutral wording: "This holds for every kind of
   external target a document can name, however it is written." Caveat: because
   T2–T4 are hidden siblings, deleting the list would make those assertions
   underivable and turn the task unfair. Keep the list as a *scope* statement;
   accept the discovery hint as the fairness price.
3. **Functional-test list.** "a reference into a sub-directory of the prompt's
   directory; a structured reference (JSON or YAML) that must still be returned
   as parsed, structured data ...; an included text fragment, an inherited base
   document, and a child-prompt tool whose target lives inside the prompt's
   directory" maps one-to-one onto the five functional tests. Neutral wording:
   "Legitimate references that stay inside the prompt's own directory must keep
   behaving exactly as they do today, including structured data; the examples
   are illustrative."
4. **Fixture-like example names.** "a prompt that pulls in `shared-config.json`
   sitting beside it, or a fragment from a `partials/` sub-folder" paraphrases
   the hidden fixtures `shared_connection.json` and `frags/`. Neutral wording:
   "a shared JSON config beside the prompt or a text fragment in a sub-folder".
5. **Fix mechanism in the title.** "contain external file references" names the
   containment approach. Neutral: "Prompt loader: external references must stay
   inside the prompt directory".
6. **Variant hint.** "Fix the underlying problem and its close variants, not
   just the exact example" tells the solver a variant set exists. Neutral:
   "Fix the underlying problem, not just the example."
7. **Mechanism wording.** "the loader reads it relative to the prompt file's own
   directory" names the component. This is descriptive, not a leak of file or
   function names; low priority.

No file names, function names, advisory IDs or flaw counts appear in
`instruction.md`; the manifest's `leak_terms` are absent.

---

## 4. Realism (quality, non-blocking)

- **T1** is the published-fix site in real upstream code (`loader.py:164`),
  reached through `prompty.load()`; realistic and reachable.
- **T2** is real, unmodified upstream (`executor.py:155`), reached through
  `prompty.load()` and OpenAI wire projection. The hidden test calls the private
  `_project_prompty_tool` directly rather than a public render/wire call; that
  matches the repo's own test style (`test_tool_dispatch.py` does the same), but
  it is one layer below the stated public entry point. Not planted-looking, but
  worth remembering that a solver reading only `load()` may not see it.
- **T3/T4 are injected siblings**, as `notes.md` and `manifest.json`
  (`injected_siblings`) state. From the patch context both read as ordinary
  composition features: `${prompt:}` delegates the join/read to
  `utils.load_fragment`, and `base:` recurses through `load_prompty` and merges
  with `setdefault`. Nothing looks like a test hook. However, they are
  synthetic by construction and the shipped `/app` tree is not in this checkout,
  so their style, documentation and reachability cannot be independently
  confirmed here. Recommend one source-level read-through of the two injected
  branches to confirm they look native and are exercised by a visible repo path.
- `tests/test.sh` runs the pristine project suite from `/tests`, and
  `test_load_file_not_found_raises` writes a temporary prompt into
  `/tests/functional/project/prompts`. That requires the verifier tree to be
  writable (the builder's runs confirm it is). If `/tests` were ever mounted
  read-only, every fix would fail one project test.

---

## 5. Verdict

### a. Unfairness gate — **NOT READY**

Mechanism: **contradiction between instruction and one test's harness**, not
leniency.

`security/test_file_reference_containment.py::test_prompty_tool_child_path_traversal`
does:

```python
agent = prompty.load(parent)
tool = agent.tools[0]

def call():
    return repr(_project_prompty_tool(tool, agent))

_assert_blocked(token, call)
```

The load and tool extraction happen outside the refusal-tolerant wrapper. A
correct, fail-closed fix that validates child-prompt paths while loading the
document (for example in `_pre_process`/`_build_agent` or in the `Prompty`
model) raises `ValueError` from `prompty.load(parent)`; that exception is not
caught, the test errors, `score.py` records a security failure, and reward is 0.
Such a fix blocks every out-of-directory read, preserves every legitimate
in-directory child (the functional and project cases still load), and is
exactly what I-P2 describes — "When a path would escape the prompt's directory,
loading fails with a client-side error". The instruction never says the refusal
must be deferred to wire projection, and it describes the loader itself as the
reader of all four reference kinds. The test therefore rejects a correct fix
that the instruction invites.

**Exact required test change** (the only change needed to clear the gate): move
the load and projection into `call()` so any refusal point is tolerated:

```python
    parent.write_text(...)

    def call():
        agent = prompty.load(parent)
        return repr(_project_prompty_tool(agent.tools[0], agent))

    _assert_blocked(token, call)
```

This still fails on the injected (vulnerable) tree — `prompty.load` succeeds and
the projection leaks the token — and passes on the oracle. Alternatively, the
instruction would have to say that the child reference is resolved only when the
tool is projected and that eager load-time refusal is not acceptable; the test
change is cleaner and leaks no internals.

No other test has a "correct fix fails" mechanism. The remaining risks are
quality-only.

### b. Quality to tighten (non-blocking)

1. **Add a security test for the dispatch route.** Write a parent with
   `kind: prompty, path: ../secret.prompty` and drive
   `PromptyToolHandler._resolve_child_path` / `dispatch_tool`, asserting the
   token never leaks. The oracle patches `tool_dispatch.py:277` but no test
   covers it, so a fix that only touches `executor.py:155` passes while the
   execution read stays open.
2. **Require a client error.** Add a strict variant of each escaping case that
   asserts an exception; `_assert_blocked` currently accepts a silent no-op,
   contrary to I-P2.
3. **Detect read-before-refuse.** Patch `builtins.open`/`os.open` (or place a
   decoy that errors on read) and assert the escaping path is never opened;
   today a read-then-raise fix passes though I-P2 forbids partial reads.
4. **Fix #1 above is also the gate-a fix** — move `prompty.load(parent)` inside
   `call()` in `test_prompty_tool_child_path_traversal`.
5. **Hints:** neutralize the spellings parenthetical, the fixture-like
   `shared-config.json`/`partials/` example, the "close variants" sentence and
   the title's "contain"; keep the four-sink list for fairness but reframe it as
   scope (section 3).
6. **Realism:** read through the two injected siblings in the shipped tree to
   confirm they look native; T1/T2 are genuine upstream. Keep the writable
   `/tests` assumption in mind for `test_load_file_not_found_raises`.
