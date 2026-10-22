# Dependency manager: package binaries

## System

This project is a command-line dependency manager for a programming ecosystem. A
project lists the third-party packages it depends on, and the tool downloads each
one into a per-package install directory under the shared install area. A package
may declare one or more "binaries": helper scripts or executables shipped with the
package. When the tool installs or refreshes a package, it makes each declared
binary runnable — it marks the binary file executable and creates a small launcher
("proxy") for it in the project's shared binary directory so the user can invoke it
by name.

The binaries a package declares, and the files they point at, are controlled by
whoever authored that package — i.e. by the remote dependency, not by the user who
runs the install.

## Observed impact

A user adds a dependency and runs the install command (for example
`install`, `update` or `reinstall` from the CLI). While making that package's
declared binaries runnable, the tool follows a binary entry that actually refers to
a file **outside** the package's own install directory, and changes that outside
file's permissions (making it world-executable). Because the path and its target
are chosen by the package author, a hostile dependency can get the tool to flip the
permissions of a file elsewhere on the machine running the install — a file that has
nothing to do with the package.

## Security properties (invariants)

- No binary a package declares may cause the tool to read, mark executable, proxy,
  or otherwise act on any file that lies outside that package's own install
  directory. This holds no matter how the escape is expressed — whether the declared
  path steps up and out of the directory, or names an in-directory file that is
  itself a link leading outside it — and no matter which install, download or
  refresh step is the one that would touch the file.
- If the tool cannot determine with certainty that a declared binary resolves to a
  real location inside the package's install directory, it must not act on it.
- A binary that genuinely lives inside the package's install directory must keep
  working exactly as today. This includes a binary that is an in-package link whose
  target is also inside the package, and a package whose install directory is itself
  reached through a link (as when a dependency is installed from a local path).

## Refusal form

When a declared binary would escape the package directory, the tool skips just that
binary (optionally warning) and continues; it does not abort the whole install, and
it produces no side effect for the skipped entry — no permission change and no
launcher. Skipping one bad entry must not affect the handling of the package's other,
legitimate binaries.

## Constraints

- Fix the problem and its close variants, not only the single example above.
- Keep every legitimate use working; a magnitude check: a package that declares an
  ordinary in-package binary, or a package installed from a local path, must install
  its binaries and run exactly as before.
- Do not modify or add tests, and do not special-case the example input.
- Do not look up the upstream advisory or fix; solve it from the code.

Examples in this report are examples, not the complete set of inputs the fix must
handle.
