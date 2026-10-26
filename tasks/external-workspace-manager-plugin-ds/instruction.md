# Workspace paths can escape the disk

The External Workspace Manager plugin gives a Jenkins Pipeline a workspace on a shared disk: a
build allocates a workspace, and a block then runs inside it. Where that workspace lives on the
disk is decided from values the build supplies.

A Pipeline can allocate a workspace with a relative path such as `../team-b` and then run a block
in it. The block's files are created in a sibling directory outside the disk's mount point.

## What must hold

The plugin must never act on a filesystem location outside a disk's mount point, whatever value a
build supplies and however that value reaches it, including a value that was recorded earlier.

A refused request is a failed build or a 4xx response, and it must leave everything outside the
mount point unchanged. A server error is not a refusal.

Everything that works today keeps working: relative nested workspace paths, names that merely
contain dots, and a value recorded earlier keep behaving exactly as they do today.

These requirements apply to the plugin as a whole, not only to the example above.

There is no network access.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix or any existing implementation. Do not special-case the example.
