# Trestle commands write and delete files outside the workspace

compliance-trestle (`trestle`) manages compliance content (OSCAL catalogs, profiles, component definitions, system security plans and governed markdown documents) as files inside a trestle workspace, the directory set up by `trestle init`. Many commands take a name that the user chooses for something the command produces, and trestle places that result inside the workspace. The same is true of names trestle takes from the content it is working on rather than from the command line. In practice these names come from CI pipelines, shared scripts, imported model files and contributors who should only ever be able to affect the workspace they run in.

## Observed impact

Inside a workspace at `/work/ws` that holds a catalog named `nist`:

```
trestle author catalog-generate -n nist -o /tmp/elsewhere
```

This writes the generated control markdown into `/tmp/elsewhere`, outside the workspace. With `--force-overwrite`, an existing directory at that location is deleted first, even when the command then fails.

## Required behaviour

- No name trestle turns into a path under the workspace, whatever that name is, how it is spelled or where it comes from, may cause a file or directory outside the workspace the command runs in to be created, modified or deleted.
- The boundary is the workspace the command runs in. Any location not inside that workspace counts as outside, whatever it contains, including another trestle workspace.
- A name that would land outside makes the command fail with a non-zero exit status. Nothing outside the workspace may be created, changed or removed, including before the command fails.

The command above is one example, not the full set. The rule has to hold for every name trestle turns into a path, on every command that does so.

## Must keep working exactly as today

- Names that stay inside the workspace, including nested ones such as `-o markdown/catalogs/nist` or a task name such as `policies/access`.
- Choosing a name for a generated document or folder inside the task it belongs to.
- `--force-overwrite` on a folder inside the workspace, and re-running a command so that it replaces its own earlier result inside the workspace.
- Validating governed documents across the whole workspace without naming a task.
- Names that trestle refuses today must still be refused.
- The project's existing test suite.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
