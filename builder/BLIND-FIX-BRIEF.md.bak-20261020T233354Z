# Blind-fix brief (gate requirement, BUILDER.md 3f)

You are an engineer who has received a vulnerability report. You see ONLY:
- `WORK/instruction.md` (the report), and
- the vulnerable repository at `WORK/app/` (plus any helper jars in `WORK/libs/`).

Rules (this check proves the task is fair and findable from the report alone):
1. Do NOT open anything under `/Users/dev/terminal-bench/cwe-bench/` (tasks, tests, build notes, the
   reference fix) or `~/.tb-graders/` outside `WORK/`. Do not search the web or look up the upstream
   fix. Read only the report and the repository.
2. Fix the vulnerability in `WORK/app/` so that the report's attack and its close variants no longer
   work, every security property the report states holds, and legitimate use keeps working exactly
   as stated. Change source only, not tests.
3. Verify what you can locally: write your own small probes or tests under `WORK/probe/` (outside
   `app/`), compile and run them if the toolchain allows. Do not start Docker.
4. When done, write the patch: `cd WORK && diff -ruN pristine app > WORK/blind.patch`, then make
   its paths `a/...` and `b/...` relative to the repository root (the gate applies it with
   `patch -p1` inside `/app`). Check that it applies cleanly with `patch -p1 --dry-run` to a fresh
   copy of `pristine`.
5. Then, separately, answer in `WORK/mechanisms.md`: list every distinct code mechanism or path
   you believe the report covers and that you changed, one line each, and say which ones the
   report's wording itself pointed you to, as opposed to ones you found by reading the code.

Return: the patch path, a 5-line summary of the fix, and the mechanisms list.
