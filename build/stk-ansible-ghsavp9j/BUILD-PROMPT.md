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

Project root: `/home/mara/cwe-bench`. Task: `stk-ansible-ghsavp9j`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-g4mq-6fp5-qwcf; GHSA-vp9j-rghq-8jhh
- Pinned (vulnerable) commit: 378434a148558c6f2d80e430aee3d5c7c3773bf3. Published fix: 80b9a0a25c5f, 8251d9f4c2bc, ecf99d5e1ff7, 77d0effcc5b2, 84afa8e90cd1, ffd3757fc354.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-vp9j-rghq-8jhh",
 "pattern": "H3b1",
 "repo": "ansible/ansible",
 "pinned_commit": "378434a148558c6f2d80e430aee3d5c7c3773bf3",
 "protections": [
  "P1: decrypted vault content written to a file must be created owner-only (0600); the earlier guard is a process-wide os.umask(0o077) in the ansible-vault CLI (lib/ansible/cli/vault.py:145-146, restored at 242-243) plus mkstemp for the edit temp (lib/ansible/parsing/vault/__init__.py:853).",
  "P2: the file that receives decrypted content must stay the same securely-created inode; it must not be unlinked and re-opened by name, or another local user can interpose a file/symlink (mkstemp at lib/ansible/parsing/vault/__init__.py:853 versus os.remove+open at 1076-1082).",
  "P3: decrypted temporary files must be destroyed after use (_shred_file at lib/ansible/parsing/vault/__init__.py:815-846, called at 865 and 872).",
  "P4 (must keep working): re-encrypting/editing an existing vault file preserves the destination's mode/ownership (lib/ansible/parsing/vault/__init__.py:1094-1097 and 1020-1022)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/ansible/cli/vault.py:145",
    "lib/ansible/cli/vault.py:146",
    "lib/ansible/parsing/vault/__init__.py:848",
    "lib/ansible/parsing/vault/__init__.py:859",
    "lib/ansible/parsing/vault/__init__.py:922",
    "lib/ansible/parsing/vault/__init__.py:1044",
    "lib/ansible/parsing/vault/__init__.py:1076",
    "lib/ansible/parsing/vault/__init__.py:1081"
   ],
   "reason_to_dismiss": "ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/ansible/cli/vault.py:145",
    "lib/ansible/cli/vault.py:146",
    "lib/ansible/cli/vault.py:240",
    "lib/ansible/cli/vault.py:243",
    "lib/ansible/parsing/vault/__init__.py:859",
    "lib/ansible/parsing/vault/__init__.py:922",
    "lib/ansible/parsing/vault/__init__.py:1076",
    "lib/ansible/parsing/vault/__init__.py:1080",
    "lib/ansible/parsing/vault/__init__.py:1081",
    "test/units/parsing/vault/test_vault_editor.py:112",
    "test/units/parsing/vault/test_vault_editor.py:182"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "lib/ansible/parsing/vault/__init__.py:853",
    "lib/ansible/parsing/vault/__init__.py:859",
    "lib/ansible/parsing/vault/__init__.py:1076",
    "lib/ansible/parsing/vault/__init__.py:1080",
    "lib/ansible/parsing/vault/__init__.py:1081"
   ],
   "reason_to_dismiss": "mkstemp already created the temp file with a random name and mode 0600 in a sticky /tmp, so refilling that same temp file cannot be read or redirected by another local user.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "xhard",
   "tier_mimo": "xhard",
   "type": "deepseek",
   "evidence": [
    "lib/ansible/parsing/vault/__init__.py:851",
    "lib/ansible/parsing/vault/__init__.py:853",
    "lib/ansible/parsing/vault/__init__.py:854",
    "lib/ansible/parsing/vault/__init__.py:859",
    "lib/ansible/parsing/vault/__init__.py:868",
    "lib/ansible/parsing/vault/__init__.py:1076",
    "lib/ansible/parsing/vault/__init__.py:1080",
    "lib/ansible/parsing/vault/__init__.py:1081",
    "lib/ansible/parsing/dataloader.py:325",
    "lib/ansible/parsing/dataloader.py:326"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/ansible/parsing/dataloader.py:323",
    "lib/ansible/parsing/dataloader.py:325",
    "lib/ansible/parsing/dataloader.py:369",
    "lib/ansible/parsing/dataloader.py:377"
   ],
   "reason_to_dismiss": "DataLoader writes the decrypted vault data through the mkstemp fd (mode 0600) and only unlinks it at cleanup, so it is not the racy remove/reopen pattern; a fix aimed at ansible-vault edit need not touch this second implementation.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "lib/ansible/parsing/dataloader.py:323",
    "lib/ansible/parsing/dataloader.py:325",
    "lib/ansible/parsing/dataloader.py:326",
    "lib/ansible/parsing/dataloader.py:369",
    "lib/ansible/parsing/dataloader.py:370",
    "lib/ansible/parsing/dataloader.py:384",
    "lib/ansible/config/manager.py:118",
    "lib/ansible/config/manager.py:122",
    "lib/ansible/config/manager.py:124",
    "lib/ansible/plugins/action/__init__.py:441"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/ansible/parsing/vault/__init__.py:856",
    "lib/ansible/parsing/vault/__init__.py:862",
    "lib/ansible/parsing/vault/__init__.py:865",
    "lib/ansible/parsing/vault/__init__.py:868",
    "lib/ansible/parsing/vault/__init__.py:878"
   ],
   "reason_to_dismiss": "If reading or encrypting the edited data fails the command aborts, so a leftover plaintext file is harmless; the editor-error and no-change paths already shred the temp file.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/ansible/parsing/vault/__init__.py:856",
    "lib/ansible/parsing/vault/__init__.py:857",
    "lib/ansible/parsing/vault/__init__.py:862",
    "lib/ansible/parsing/vault/__init__.py:863",
    "lib/ansible/parsing/vault/__init__.py:865",
    "lib/ansible/parsing/vault/__init__.py:868",
    "lib/ansible/parsing/vault/__init__.py:871",
    "lib/ansible/parsing/vault/__init__.py:872",
    "lib/ansible/parsing/vault/__init__.py:878",
    "lib/ansible/parsing/vault/__init__.py:879",
    "lib/ansible/parsing/vault/__init__.py:815",
    "lib/ansible/parsing/vault/__init__.py:846"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/ansible/parsing/vault/__init__.py:1084",
    "lib/ansible/parsing/vault/__init__.py:1090",
    "lib/ansible/parsing/vault/__init__.py:1091",
    "lib/ansible/parsing/vault/__init__.py:1096",
    "lib/ansible/parsing/vault/__init__.py:1097",
    "lib/ansible/parsing/vault/__init__.py:1018",
    "lib/ansible/parsing/vault/__init__.py:1020",
    "lib/ansible/parsing/vault/__init__.py:1021"
   ],
   "reason_to_dismiss": "The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "lib/ansible/parsing/vault/__init__.py:1084",
    "lib/ansible/parsing/vault/__init__.py:1087",
    "lib/ansible/parsing/vault/__init__.py:1090",
    "lib/ansible/parsing/vault/__init__.py:1091",
    "lib/ansible/parsing/vault/__init__.py:1094",
    "lib/ansible/parsing/vault/__init__.py:1096",
    "lib/ansible/parsing/vault/__init__.py:1097",
    "lib/ansible/parsing/vault/__init__.py:1018",
    "lib/ansible/parsing/vault/__init__.py:1020",
    "lib/ansible/parsing/vault/__init__.py:1021",
    "lib/ansible/parsing/vault/__init__.py:1022"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "The earlier hardening (umask 0o077 at lib/ansible/cli/vault.py:146 and mkstemp at lib/ansible/parsing/vault/__init__.py:853) masks the residual defect: because the temp file is created 0600, the unlink+recreate at lib/ansible/parsing/vault/__init__.py:1076-1082 no longer looks like an insecure-temp-file problem, so the mode loss and the race window are easy to overlook."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "Forcing 0600 on every file that write_data recreates collides with shuffle_files/rekey_file restoring the destination's mode and ownership (lib/ansible/parsing/vault/__init__.py:1094-1097, 1020-1022); the owner-only rule has to be scoped to plaintext writes only."
  },
  {
   "a": "T2",
   "b": "T5",
   "what": "Closing the temp race with O_EXCL/O_NOFOLLOW on every open would break the supported symlink-following behaviour of encrypt/decrypt/edit (lib/ansible/parsing/vault/__init__.py:904, 913, 942, 989; tests at test/units/parsing/vault/test_vault_editor.py:289-304, 362-395)."
  }
 ],
 "fairness_risks": [
  "A blanket 'all vault files must be 0600' rule contradicts the must-keep-working mode/ownership preservation for encrypted destinations (lib/ansible/parsing/vault/__init__.py:1094-1097, 1020-1022).",
  "Refusing symlink destinations (O_NOFOLLOW) breaks encrypting/decrypting/editing a vault file through a symlink, which is supported and tested (lib/ansible/parsing/vault/__init__.py:904, 913, 942, 989 and the 'follow the symlink' comments; test/units/parsing/vault/test_vault_editor.py:289-304, 362-395).",
  "The '-' stdout pseudo-filename and special paths such as /dev/null must keep working (lib/ansible/parsing/vault/__init__.py:887-891, 1073-1074; test/units/parsing/vault/test_vault_editor.py:480-492); a rule that chmods or refuses non-regular outputs would break them.",
  "An unchanged edit must leave the encrypted file byte-identical (lib/ansible/parsing/vault/__init__.py:870-873; test/units/parsing/vault/test_vault_editor.py:169-186); a fix must not re-encrypt or shred the destination on that path."
 ],
 "effort_minutes": 60,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T5"
  ],
  "why": "Four independent fix sites. T1+T2 are one shared-guard group (the CLI-only umask and the write_data unlink/reopen in the same write path): the deepseek-trap is that the umask/mkstemp story sounds complete, while the library entry points and the recreated inode are not covered. T3 is a second implementation of 'decrypt vault data to a temp file' that a fix aimed only at ansible-vault would miss. T4 is the absent cleanup route that only exists after the editor returns. T5 is the mimo-type coupled value: over-hardening every mode to 0600 breaks the deliberate mode/ownership preservation, so the solver must scope the rule to plaintext. This mix needs four separate judgements instead of one blanket permissions change."
 },
 "unverified": [
  "The exact diff of the 2022 fix commits (77d0effcc5b2, 84afa8e90cd1, ffd3757fc354) could not be read: the sandbox has no shell/git and the object database is outside the permitted path, so the residual sites were derived from the pinned code only.",
  "Whether the earlier fix introduced the os.umask(0o077) block (lib/ansible/cli/vault.py:145-146) or the mkstemp temp (lib/ansible/parsing/vault/__init__.py:853) cannot be attributed from the worktree; both guards are present in the pinned code.",
  "Related but not counted: the persistent-connection control directory is created without an explicit mode (lib/ansible/cli/scripts/ansible_connection_cli_stub.py:261-262, default ~/.ansible/pc in lib/ansible/config/base.yml:1639-1646) and the AF_UNIX socket is bound without chmod (lines 108-109); that is the same 'expose resource to wrong sphere' family but belongs to a different advisory.",
  "_shred_file resolves 'shred' through PATH (lib/ansible/parsing/vault/__init__.py:833), an untrusted-search-path concern outside CWE-362/377/668 and not counted.",
  "ansible-vault encrypt_string accepts --output (lib/ansible/cli/vault.py:66, 96-97) but execute_encrypt_string never writes output_file; this is a functional gap, not a temp-file exposure, and is not counted."
 ]
}
  ```
- Published fix sites:   - lib/ansible/parsing/vault/__init__.py:853 — T2 M8 (reason to dismiss: mkstemp already created the temp file with a random name and mode 0600 in a sticky /tmp, so refilling that same temp file cannot be read or redirected by another local user.)
  - lib/ansible/parsing/vault/__init__.py:859 — T2 M8 (reason to dismiss: mkstemp already created the temp file with a random name and mode 0600 in a sticky /tmp, so refilling that same temp file cannot be read or redirected by another local user.)
  - lib/ansible/parsing/vault/__init__.py:1076 — T2 M8 (reason to dismiss: mkstemp already created the temp file with a random name and mode 0600 in a sticky /tmp, so refilling that same temp file cannot be read or redirected by another local user.)
  - lib/ansible/parsing/vault/__init__.py:1080 — T2 M8 (reason to dismiss: mkstemp already created the temp file with a random name and mode 0600 in a sticky /tmp, so refilling that same temp file cannot be read or redirected by another local user.)
  - lib/ansible/parsing/vault/__init__.py:1081 — T2 M8 (reason to dismiss: mkstemp already created the temp file with a random name and mode 0600 in a sticky /tmp, so refilling that same temp file cannot be read or redirected by another local user.)
  - lib/ansible/parsing/dataloader.py:323 — T3 M2 (reason to dismiss: DataLoader writes the decrypted vault data through the mkstemp fd (mode 0600) and only unlinks it at cleanup, so it is not the racy remove/reopen pattern; a fix aimed at ansible-vault edit need not touch this second implementation.)
  - lib/ansible/parsing/dataloader.py:325 — T3 M2 (reason to dismiss: DataLoader writes the decrypted vault data through the mkstemp fd (mode 0600) and only unlinks it at cleanup, so it is not the racy remove/reopen pattern; a fix aimed at ansible-vault edit need not touch this second implementation.)
  - lib/ansible/parsing/dataloader.py:369 — T3 M2 (reason to dismiss: DataLoader writes the decrypted vault data through the mkstemp fd (mode 0600) and only unlinks it at cleanup, so it is not the racy remove/reopen pattern; a fix aimed at ansible-vault edit need not touch this second implementation.)
  - lib/ansible/parsing/dataloader.py:377 — T3 M2 (reason to dismiss: DataLoader writes the decrypted vault data through the mkstemp fd (mode 0600) and only unlinks it at cleanup, so it is not the racy remove/reopen pattern; a fix aimed at ansible-vault edit need not touch this second implementation.)
  - lib/ansible/parsing/vault/__init__.py:1084 — T5 M11 (reason to dismiss: The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.)
  - lib/ansible/parsing/vault/__init__.py:1090 — T5 M11 (reason to dismiss: The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.)
  - lib/ansible/parsing/vault/__init__.py:1091 — T5 M11 (reason to dismiss: The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.)
  - lib/ansible/parsing/vault/__init__.py:1096 — T5 M11 (reason to dismiss: The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.)
  - lib/ansible/parsing/vault/__init__.py:1097 — T5 M11 (reason to dismiss: The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.)
  - lib/ansible/parsing/vault/__init__.py:1018 — T5 M11 (reason to dismiss: The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.)
  - lib/ansible/parsing/vault/__init__.py:1020 — T5 M11 (reason to dismiss: The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.)
  - lib/ansible/parsing/vault/__init__.py:1021 — T5 M11 (reason to dismiss: The bytes shuffle_files/rekey_file put in place are already ciphertext, and restoring the destination's mode and ownership is deliberate; a blanket 0600 rule here would silently change the users' file modes.)
- Uncovered routes to confirm (pattern B):   - lib/ansible/cli/vault.py:145 — T1 M1 (reason to dismiss: ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.)
  - lib/ansible/cli/vault.py:146 — T1 M1 (reason to dismiss: ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.)
  - lib/ansible/parsing/vault/__init__.py:848 — T1 M1 (reason to dismiss: ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.)
  - lib/ansible/parsing/vault/__init__.py:859 — T1 M1 (reason to dismiss: ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.)
  - lib/ansible/parsing/vault/__init__.py:922 — T1 M1 (reason to dismiss: ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.)
  - lib/ansible/parsing/vault/__init__.py:1044 — T1 M1 (reason to dismiss: ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.)
  - lib/ansible/parsing/vault/__init__.py:1076 — T1 M1 (reason to dismiss: ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.)
  - lib/ansible/parsing/vault/__init__.py:1081 — T1 M1 (reason to dismiss: ansible-vault sets umask 0o077 before running the action and the edit temp comes from mkstemp, so temp/output files are already owner-only; nothing needs to change in the library.)
  - lib/ansible/parsing/vault/__init__.py:856 — T4 M4 (reason to dismiss: If reading or encrypting the edited data fails the command aborts, so a leftover plaintext file is harmless; the editor-error and no-change paths already shred the temp file.)
  - lib/ansible/parsing/vault/__init__.py:862 — T4 M4 (reason to dismiss: If reading or encrypting the edited data fails the command aborts, so a leftover plaintext file is harmless; the editor-error and no-change paths already shred the temp file.)
  - lib/ansible/parsing/vault/__init__.py:865 — T4 M4 (reason to dismiss: If reading or encrypting the edited data fails the command aborts, so a leftover plaintext file is harmless; the editor-error and no-change paths already shred the temp file.)
  - lib/ansible/parsing/vault/__init__.py:868 — T4 M4 (reason to dismiss: If reading or encrypting the edited data fails the command aborts, so a leftover plaintext file is harmless; the editor-error and no-change paths already shred the temp file.)
  - lib/ansible/parsing/vault/__init__.py:878 — T4 M4 (reason to dismiss: If reading or encrypting the edited data fails the command aborts, so a leftover plaintext file is harmless; the editor-error and no-change paths already shred the temp file.)
- Design plan from the lead: TRACK = STACKED (H3b1). Build the stacked design the reader chose: traps T1, T2, T3, T4, T5. Why: Four independent fix sites. T1+T2 are one shared-guard group (the CLI-only umask and the write_data unlink/reopen in the same write path): the deepseek-trap is that the umask/mkstemp story sounds complete, while the library entry points and the recreated inode are not covered. T3 is a second implementation of 'decrypt vault data to a temp file' that a fix aimed only at ansible-vault would miss. T4 is the absent cleanup route that only exists after the editor returns. T5 is the mimo-type coupled value: over-hardening every mode to 0600 breaks the deliberate mode/ownership preservation, so the solver must scope the rule to plaintext. This mix needs four separate judgements instead of one blanket permissions change. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): A blanket 'all vault files must be 0600' rule contradicts the must-keep-working mode/ownership preservation for encrypted destinations (lib/ansible/parsing/vault/__init__.py:1094-1097, 1020-1022). | Refusing symlink destinations (O_NOFOLLOW) breaks encrypting/decrypting/editing a vault file through a symlink, which is supported and tested (lib/ansible/parsing/vault/__init__.py:904, 913, 942, 989 and the 'follow the symlink' comments; test/units/parsing/vault/test_vault_editor.py:289-304, 362-395). | The '-' stdout pseudo-filename and special paths such as /dev/null must keep working (lib/ansible/parsing/vault/__init__.py:887-891, 1073-1074; test/units/parsing/vault/test_vault_editor.py:480-492); a rule that chmods or refuses non-regular outputs would break them. | An unchanged edit must leave the encrypted file byte-identical (lib/ansible/parsing/vault/__init__.py:870-873; test/units/parsing/vault/test_vault_editor.py:169-186); a fix must not re-encrypt or shred the destination on that path.. Conflicts the reader found: Forcing 0600 on every file that write_data recreates collides with shuffle_files/rekey_file restoring the destination's mode and ownership (lib/ansible/parsing/vault/__init__.py:1094-1097, 1020-1022); the owner-only rule has to be scoped to plaintext writes only. | Closing the temp race with O_EXCL/O_NOFOLLOW on every open would break the supported symlink-following behaviour of encrypt/decrypt/edit (lib/ansible/parsing/vault/__init__.py:904, 913, 942, 989; tests at test/units/parsing/vault/test_vault_editor.py:289-304, 362-395).

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

## Environment (`tasks/stk-ansible-ghsavp9j/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-ansible-ghsavp9j/instruction.md`)
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

## Tests (`tasks/stk-ansible-ghsavp9j/tests/`)
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
- **Wrong-fix patches** go in `build/stk-ansible-ghsavp9j/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-ansible-ghsavp9j/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-ansible-ghsavp9j/manifest.json`:**
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

**Also in `build/stk-ansible-ghsavp9j/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-ansible-ghsavp9j --only static
python3 -I common/gate/gate.py stk-ansible-ghsavp9j --only nop
python3 -I common/gate/gate.py stk-ansible-ghsavp9j --only oracle
python3 -I common/gate/gate.py stk-ansible-ghsavp9j --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-ansible-ghsavp9j/`;
  - edit only `tasks/stk-ansible-ghsavp9j/`, `build/stk-ansible-ghsavp9j/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-vp9j-rghq-8jhh.json`. Verify each trap on the
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

Stacked task slug: `stk-ansible-ghsavp9j`. Control task slug: `stk-ansible-ghsavp9j-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-vp9j-rghq-8jhh.json`.
