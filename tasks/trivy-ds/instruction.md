# A plugin's name can reach outside Trivy's plugin directory

Trivy is a security scanner. It supports plugins: separate programs that add a scanner, an output format or a subcommand. A plugin is installed from a local path, a URL or an archive, and Trivy keeps it in a plugin directory under its data home. Each plugin ships a small metadata file that records its name and how to run it; Trivy reads that metadata when it installs the plugin and stores a copy next to the installed files.

## Observed impact

Installing a plugin whose packaged metadata declares the name `../escaped_plugin` creates a plugin directory above the plugin directory and deletes whatever was already stored there. The crafted metadata is the attacker input; no unusual command-line option is needed.

## Properties that must hold

- No plugin name — however Trivy obtained it, and whichever plugin management operation uses it — may cause a file or directory outside the plugin directory to be created, written, removed, read or executed.
- A name that leaves the plugin directory only after its path is interpreted, including one that goes through a link that already exists inside the plugin directory, is covered as well.
- A name that would escape must be refused or treated as absent: the operation may return an error or do nothing, and in either case it must leave everything outside the plugin directory untouched.
- A name that stays inside the plugin directory keeps working exactly as it does today, including the files each management operation writes inside it and the programs it starts from there.

## Legitimate use that must not regress

- An install source is a filesystem path or a URL; it normally contains `/` and is not itself a plugin name.
- A source that wraps the plugin files in a single top-level directory is still unwrapped.
- Removing a plugin that is not installed still succeeds without an error.
- Updating the index still succeeds and still stores the downloaded index, even when its contents cannot be parsed.
- The package's exported Go API keeps its current shape: the constructor, its options and the exported methods.

The command, the name and the values above are examples, not a complete list of the ways the problem can be reached.

## Constraints

- Fix the reported problem and its close variants; do not special-case the example.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix or the security advisory for this issue.
