# FAIRNESS — langchain-path-escape-inj

Reviewer: pre-trial fairness/leniency review (BUILDER.md 3h). Static review only;
nothing was run. Inputs read: instruction.md, all of tests/ (security, functional,
functional/project, test.sh), solution/fix.patch, environment/injection.patch,
manifest.json, notes.md, checks/*.patch.

## 1. Per-test fairness

### Security (tests/security)

| Test | Asserts | Instruction basis | Correct fix could fail? | Risk |
|---|---|---|---|---|
| test_file_search_escape.py::test_glob_pattern_upward_traversal | glob `../TOKEN.txt` from `/` raises or does not surface the token | "a relative pattern or path that walks upward" (Invariants, bullet 1) | no. Rejecting `..` segments and per-match resolve+containment both pass, and so does raising | low |
| test_file_search_escape.py::test_glob_symlink_file_escape | `*.txt` doesn't list an in-root symlink whose target is outside | "a symbolic link inside the workspace whose target lies outside it" | no | low |
| test_file_search_escape.py::test_grep_symlink_file_content_escape | python-backend grep doesn't return content read through an outward symlink | same sentence; "for every one of these operations" | no | low |
| test_file_tool_escape.py::test_filesystem_sibling_prefix_escape | fs memory tool, prefix `/memories`, `view /memories_sibling/note.txt` doesn't return the token | Invariants bullet 2 (sibling sharing leading characters) | no | low |
| test_file_tool_escape.py::test_state_sibling_prefix_escape | same, state-backed variant | bullet 2 + "Either variant can be restricted" | no | low |
| test_file_tool_escape.py::test_copy_source_symlink_escape | `copy /link.txt -> /stolen.txt` (link points outside) leaks the token in neither reply nor destination | "read, list, enumerate, copy or write"; symlink sentence | no. Resolve-then-contain and refusing symlinked sources both pass | low |
| test_file_tool_escape.py::test_list_sibling_prefix_escape | state `glob /memories` doesn't list `/memories_sibling/...` | bullet 2; "list" | no | low |

### Functional (tests/functional)

| Test | Asserts | Instruction basis | Correct fix could fail? | Risk |
|---|---|---|---|---|
| test_file_search_legit.py::test_glob_simple_pattern | `*.py` → `/a.py`, not b.txt | Keep working: "a glob such as `*.py`" | no | low |
| …::test_glob_recursive_pattern | `**/*.py` finds `/pkg/mod.py` | "a recursive `**/…` pattern" | no | low |
| …::test_glob_filename_with_dots_substring | `v1..2.py` still listed | "a filename that merely contains dots" | no (a substring-`..` filter on match names fails, and the instruction rules that out) | low |
| …::test_glob_in_workspace_symlink_kept | an in-root→in-root symlink is listed | "a symbolic link … whose target is also inside" | no (blanket symlink drop fails, and the instruction rules that out) | low |
| …::test_glob_no_matches_contract | exactly `"No files found"` | "'nothing found' result still being returned" | no | low |
| …::test_grep_content_python_fallback | python grep finds NEEDLE | "a regex content search … same matches" | no | low |
| …::test_grep_content_default_backend | default backend finds NEEDLE | same | no | low |
| …::test_grep_in_workspace_symlink_kept | in-root symlink still matched (python backend) | symlink keep-working sentence | no. `os.walk` lists file symlinks in `files`; a resolve check keeps them | low |
| …::test_grep_no_matches_contract | exactly `"No matches found"` | "nothing found … rather than an error" | no | low |
| test_file_tool_legit.py::test_filesystem_create_and_view_in_allowed_dir | create+view `/memories/note.txt` | "keeping a note under the allowed notes directory" | no | low |
| …::test_filesystem_nested_descendant_allowed | `/memories/sub/deep.txt` works | "files nested beneath it" | no | low |
| …::test_state_view_in_allowed_dir | state view in `/memories` | same | no | low |
| …::test_copy_in_workspace | in-root copy works | "copying … continuing to work" | no | low |
| …::test_state_glob_lists_in_prefix | listing `/memories` shows both entries | "listing … continuing to work" | no | low |

### Project tests (tests/functional/project, pristine upstream)

| Test | Asserts | Instruction basis | Correct fix could fail? | Risk |
|---|---|---|---|---|
| test_anthropic_tools.py::TestPathValidation::test_allowed_prefixes, test_memories_prefix; TestFileOperations::test_path_prefix_enforcement | `ValueError` whose message matches `"Path must start with"` | none. The instruction says only "returns a client-side error" | **yes**: a fix that rewrites the prefix check and changes the message (e.g. "Path is outside the allowed directories") | **medium** |
| test_anthropic_tools.py::TestFileOperations::test_memories_prefix_enforcement | message matches `/memories` | none | yes, same reason (only if the message no longer lists the prefixes) | medium |
| test_anthropic_tools.py::TestPathValidation::test_path_traversal_blocked | message `"Path traversal not allowed"` | none (existing behaviour) | maybe: only if the solver rewrites the `..` guard's message | low–medium |
| test_file_search.py::TestPathTraversalSecurity::test_path_traversal_with_double_dots / _absolute_path / _symlink / test_validate_path_blocks_tilde / test_grep_path_traversal_protection | base-path escapes return **exactly** `"No files found"` / `"No matches found"` | contradicts Invariants bullet 3, which allows "a client-side error" | **yes**: a solver who reasonably makes the shared path validator raise on escape (allowed by the instruction) fails 5 tests | **medium** |
| remaining project tests (normalization, view/create/str_replace/insert/delete/rename, brace expansion, include filters, sorting, large-file skip, ripgrep cmd literal) | existing behaviour | "Ordinary in-workspace use must behave exactly as it does today" | no | low |

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| T1 glob (pattern) | reject `..`/absolute patterns only, no per-match check | yes: test_glob_symlink_file_escape (sf-miss-glob drops both checks) |
| T1 glob (symlink) | lexical `os.path.abspath`/`normpath` containment per match, no resolve | yes: test_glob_symlink_file_escape |
| T1 glob (symlinked **dir**) | check only `match.is_symlink()` leaves (resolve target only if the leaf is a link) | **no**: `pattern="linkdir/*"` with `linkdir → outside` leaks, and no test uses a symlinked directory in a glob pattern |
| T2 grep fallback | fix glob + ripgrep only, leave `rglob` fallback | yes: test_grep_symlink_file_content_escape (sf-miss-grep) |
| T2 grep fallback | drop all symlinks | functional: test_grep_in_workspace_symlink_kept / test_glob_in_workspace_symlink_kept (ff-overbroad) |
| T3 fs prefix | fix only the shared state `_validate_path` | yes: test_filesystem_sibling_prefix_escape (sf-miss-fsprefix) |
| T3/T4 prefix | `startswith(prefix + "/")` with no equality branch, so the allowed dir itself is rejected (over-strict) | **no**: no hidden test views or lists the bare allowed directory with a filesystem tool. The instruction promises "for that directory itself" |
| T4 state prefix | fix only the filesystem tool | yes: test_state_sibling_prefix_escape (sf-miss-stateprefix) |
| S1 copy | validate source lexically (existing `..`/`~` guard), no resolve-containment | yes: test_copy_source_symlink_escape (sf-miss-copy) |
| S2 list | rely on `_validate_path` of the argument and leave the raw-startswith filter | yes: test_list_sibling_prefix_escape (sf-miss-listglob) |
| refuse-all | treat every symlink as an escape | functional (ff-overbroad) |
| write side | patch prefix check per handler (view only) instead of in the shared validator | **no**: no create/str_replace/rename into `/memories_sibling` is tested. Low plausibility because the check lives in one helper per variant |
| ripgrep backend | no containment on rg results | not tested; manifest says it isn't reachable at the pin (rg doesn't follow links). Acceptable |

Wrong fixes no test catches: (a) a leaf-only symlink check that misses symlinked directories inside glob patterns; (b) an over-strict prefix check that rejects the allowed directory itself; (c) per-handler, view-only prefix fixes. (a) is the one worth closing.

## 3. Hints in instruction.md

1. "This holds however the input is spelled — a relative pattern or path that walks upward, an absolute path, a name that merely shares leading characters with an allowed directory, or a symbolic link inside the workspace whose target lies outside it — and for every one of these operations, not only the one first observed." This lists all the attack shapes (variant list) and says there is more than one site. Proposed: "This holds however the input is spelled and for every operation these components expose." Caveat: the sibling-prefix case is then carried by bullet 2 and the symlink case by the keep-working symlink bullet, so fairness survives the cut.
2. Invariant verb list "read, list, enumerate, copy or write" and keep-working "viewing, creating, editing, moving, copying and listing". "copy" and "listing" point straight at the two injected commands (S1, S2), because the system description lists only "view, create, edit, move and remove". Proposed: in "The system", describe the full operation set once ("view, create, edit, copy, move, list and remove files"). Then use neutral verbs in the invariant: "access, enumerate or write".
3. "an entry that belongs to a neighbouring directory outside the one the tool was limited to" (Observed problem). This paraphrases the sibling-prefix flaw. Acceptable because bullet 2 states it as a property, but it is redundant. Optional: "or an entry outside the directory the tool was limited to".
4. "One variant keeps the files on the host filesystem …; another keeps them in the agent's own conversation state." This names both T3/T4 variants. It is a system description, so it is acceptable. Mild.

No leak_terms appear in instruction.md. The flaw count is not stated.

## 4. Realism

- T1–T4 are upstream code at the pinned commit and are real.
- S1 `_handle_copy`: the comment says "Reuse the same traversal guard the other commands apply", but the code then re-implements only half of `_validate_and_resolve_path` inline and calls the real helper for the destination two lines later. A reviewer would find that a little odd, but it is plausible copy-paste. **Medium**: a careful reader may see it as planted.
- S1/S2 commands `copy` and `glob` are not part of Anthropic's text-editor or memory tool schemas. The server-side tool definition never emits them, so they are reachable only via the dispatcher's free-form `command` string. **Medium** realism concern. The code is reachable through the real public tool function, but no real model call under the official schema would send these commands. Also, a command named "glob" that does a plain prefix listing is a misnomer. Acceptable if the client accepts dispatcher-level reachability. Otherwise a short docstring/comment framing them as local extension commands would help.
- Minor inconsistency: the keep-working sentence says only a genuine `..` segment is an escape, yet the oracle keeps substring `..` rejection in the anthropic tools (`_validate_path`, the copy guard). No test exercises it, so it is harmless, but the instruction over-promises.

## 5. Verdict: NOT READY

Required changes:
1. **Error-contract conflict (medium).** Project tests require the existing messages ("Path must start with", "/memories", "Path traversal not allowed"). They also require exact "No files found"/"No matches found" for base-path escapes, while the instruction allows "a client-side error". Add to Keep working: "Inputs the components already reject today must keep being rejected exactly as they are now, with the same result or error message." Also, or instead, change Invariants bullet 3 so new refusals may be errors but existing ones keep their current form.
2. **Close leniency gap (a).** Add a security test: glob `linkdir/*` where `linkdir` is an in-workspace symlink to an outside directory holding a token file. Assert it is blocked. The oracle's per-match `resolve()` already passes it.
3. **Optional but recommended:** add a functional test that views/lists the bare allowed directory (`/memories`) with the filesystem tool (gap (b)). Apply hint rewrites 1–2 from section 3.
4. Decide on S1/S2 realism (commands outside the official tool schema). Document the acceptance, or add a framing comment in injection.patch.
