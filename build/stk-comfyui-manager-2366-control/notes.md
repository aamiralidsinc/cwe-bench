# stk-comfyui-manager-2366-control — build notes

- Start (UTC): 2026-10-22T19:16Z (same checkout and report as the stacked task).
- End (UTC): rebuilt 2026-10-23T02:59Z–2026-10-23T05:05Z after the workspace reset (the task tree was
  restored from the retained scratch worktrees and the verifier image, then re-verified end to end).

Control for `stk-comfyui-manager-2366`: the same pinned tree and the same instruction.md,
but only the advisory's own landing route (trusted state written into the web-writable
public folder) in the security tests, and a reference fix limited to that storage
protection (the published fix with its old-host enforcement removed).

- Pinned: 4 security tests fail, 6 functional tests pass (re-checked on the rebuilt tree).
- Reference (`solution/fix.patch`): 10/10 pass (re-checked on the rebuilt tree).
- Container gate after the rebuild: `static` reports only the expected missing blind patch
  (written later by the pipeline); `nop` PASSED; `oracle` PASSED (three runs); `patches` PASSED
  (all five checks matched; one infrastructure-only retry).
- Check patches (local, repeated): sf-no-protected-storage -> 4 security fail / functional
  pass; sf-reads-only -> 1 security fail / functional pass; ff-refuse-all -> 3 functional
  fail; pass-hardening and pass-alt -> 10/10.
- `tests/security/` has the four T1 shapes only; `tests/functional/` is the same six
  legitimate-behaviour tests as the stacked task.
