# ComfyUI-Manager: trusted state kept in a writable folder

## What this is

ComfyUI-Manager is the extension that installs and manages custom nodes and models for a
ComfyUI host. It keeps a small amount of its own state, including the setting that decides
which remote operations are allowed. On current ComfyUI builds the host offers an internal
location for that state which its user-file endpoints cannot reach; the state has instead
been kept under the user's public folder, which those endpoints can write.

## What was observed

A client that could reach the host's user-file endpoints planted Manager state in the public
folder. Manager treated the planted data as its own: a security level the operator had never
chosen was applied, and the client thereby caused package and node installation work that the
operator's security setting was meant to refuse.

## What must hold

Manager's own state is trusted only while it is kept where the host's user-file endpoints
cannot write. Wherever the host offers such a location, Manager must store its state there; after
carrying the operator's existing settings over once, it takes its own state only from there. That
carry-over must not weaken protection: a saved security level at or above the default, and
unrelated preferences, keep their values, while a saved level below the default may be raised.

State that those endpoints can reach must never be able to weaken protection: it may not lower
the effective security level, widen what remote operations are permitted, change what Manager
installs or trusts, or cause work to be carried out. Where nothing can be kept out of their
reach, the strongest security level is the effective one, and the value the operator saved is not
replaced by the enforced one.

## Contracts

- A refused request is a client error (4xx) and leaves no side effect: nothing is started,
  written, copied, queued or installed.
- Everything that works today keeps working.
- The example above is an example, not the full set.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the
upstream fix or an existing implementation. Do not special-case the example. There is no
network access.
