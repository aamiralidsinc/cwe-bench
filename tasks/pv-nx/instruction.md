# Self-hosted remote cache: a cached artifact can change files outside the project

Nx is a build system for monorepos. When a task's result is cached, the result is kept as an
artifact and reused instead of running the task again. With a self-hosted remote cache server
configured, those artifacts are also downloaded from that server and stored in the local cache
directory before their outputs are restored into the project.

We run Nx in CI against a self-hosted remote cache. On one run, a task result fetched from the
cache server wrote a file outside the project directory: the file appeared next to the project
root, although no task in the workspace declares that path and no build step should ever touch
it. The same artifact also brought in content that was never a declared output of the task.

## What must hold

A cache entry may only ever affect two kinds of place:

- its own directory inside the cache, and
- the declared outputs of the task it belongs to, each of which must resolve inside the project.

Whatever the entry contains, however its paths are written, and whether it is on its way into the
cache or on its way back into the project, nothing else on the machine may be created, changed or
deleted. If a request cannot satisfy this, it is refused: the unsafe part is not applied, and the
run reports the problem instead of continuing as if it had succeeded.

These requirements are part of the cache's contract:

- Nothing outside those two kinds of place is written, whether or not the rest of the artifact is
  usable.
- An artifact can only add content it actually carries; it cannot borrow or expose content from
  elsewhere on the machine.
- An output given as an absolute path is still valid when it lies inside the project: it denotes
  the same place as the equivalent project-relative path. Only outputs that resolve outside the
  project are invalid.
- An output that is itself a symbolic link stays a link with the same target, even when that
  target lies elsewhere. The link is only a pointer: nothing may be written through it. The same
  holds when the output is copied into the cache — the link is kept as a link, not as a copy of
  what it points at.
- Multiple outputs, directory outputs and glob patterns keep working, and an output that the
  artifact does not contain is skipped.
- The existing cache operations keep their public behaviour for legitimate artifacts.

The example above is one instance, not the full set. Fix the underlying problem and its close
variants rather than that particular input. Do not look up or copy the upstream fix; work from
this report and the code. Do not special-case the example, and do not break legitimate cache use
to make the example go away.
