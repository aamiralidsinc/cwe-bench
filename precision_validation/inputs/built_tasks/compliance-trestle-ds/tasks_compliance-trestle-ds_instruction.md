# Compliance commands can create or delete files outside the workspace

compliance-trestle (`trestle`) manages compliance content as files inside a trestle workspace, the directory set up for a trestle project. Its commands accept names chosen by the caller for results the command produces or replaces, and the command turns such a name into a location inside that workspace. In practice these names come from CI pipelines, shared scripts and contributors who should only ever be able to affect the workspace they run in.

## Required behaviour

No name that a user supplies to a trestle command for a result the command produces or replaces — whatever its spelling and in whichever option or mode the command receives it — may cause a file or directory outside the workspace the command runs in to be created, modified or deleted.

The workspace the command runs in is the boundary. Any location that is not inside that workspace counts as outside, whatever it contains; a name that leaves the workspace only after existing links are followed also counts as outside.

A name that would cross the boundary must make the command fail with a non-zero exit status. Nothing outside the workspace may be created, changed or removed, including before the command fails.

## Must keep working exactly as today

- Names that designate a location inside the workspace, including nested ones and names that replace the command's own earlier result there.
- Replacing an earlier result inside the workspace, including an explicitly requested overwrite of a folder.
- Operations that act across the whole workspace without being given a name for a produced location.
- Names that trestle refuses today must still be refused.
- The project's existing test suite.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case any example.
