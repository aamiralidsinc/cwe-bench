# Trivy plugin system — files escaping the plugins directory

## What this is

Trivy is an open-source security scanner. It has a plugin system that lets users
extend it with external commands. Plugins are installed by name, URL or local
path; each installed plugin lives in its own subdirectory of a single plugins
directory under the user's Trivy data directory. A small set of commands manage
plugins: installing them, removing them, listing them, and a few maintenance
operations that re-read an already-installed plugin, or prepare a cache
for one listed in the plugin index.

A plugin is distributed together with a small packaged metadata description that,
among other fields, records the plugin's own name. When a plugin is installed,
that metadata is also stored on disk alongside the plugin.

## Observed problem

Installing a plugin whose packaged metadata declares a hostile name causes Trivy
to create and overwrite files in a location of the attacker's choosing, outside
the plugins directory. Concretely, a single command such as

    trivy plugin install <source>

run against a plugin whose metadata carries a crafted name writes the plugin's
files above the plugins directory instead of inside it. Depending on which
management command is used, the same class of crafted name can also cause files
or directories outside the plugins directory to be removed or newly created.

## Security properties (invariants)

- No plugin name may cause Trivy to create, overwrite, read or delete any file
  or directory outside the plugins directory. This holds for every source a name
  can come from — a plugin's packaged metadata, a value supplied on the command
  line, metadata already stored on disk from an earlier install, or an entry in
  the plugin index — and for every plugin management operation, whether it
  installs, removes, reads, re-reads or prepares a cache for a plugin.
- A name that would escape the plugins directory must be refused with a plain
  error and no side effect: nothing outside the plugins directory is created,
  changed or removed, and no partial result is left behind.

## Keep working

These legitimate behaviours must be unchanged:

- Installing a plugin from a local filesystem path or from a URL. Such sources
  naturally contain `/` and other path characters; that is expected and must
  still work.
- A source archive that wraps the plugin inside a single top-level directory is
  unwrapped and installed normally.
- A version suffix on the install argument is accepted.
- Removing a plugin that is not installed succeeds as a no-op (it is not an
  error).
- Reading or re-reading an already-installed, normally named plugin, or
  preparing a cache for one, works exactly as today, with its files staying
  inside its own subdirectory.

The examples above are examples, not the full set of cases.

## Constraints

- Fix the underlying problem and its close variants, not just the one example
  trigger shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example values.
- Do not look up the upstream fix for this issue.
