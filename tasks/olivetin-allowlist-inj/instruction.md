# OliveTin — action execution hardening

## The system
OliveTin is a self-hosted web app that turns a small set of administrator-defined
commands into buttons. An operator configures each *action* with a command to run
(either run through a system shell, or as a direct program with its arguments) and,
optionally, a declared list of input arguments the caller may fill in. People start
actions through the web UI, the REST API, or incoming webhooks; OliveTin then runs
the configured command on the server, after substituting the caller's inputs and a
few values of its own into the command and into the command's environment.

In front of OliveTin sits an identity layer (a reverse-proxy header, a signed token,
or an OAuth2 profile) that tells OliveTin who the caller is — their login name, the
groups they belong to, and similar attributes.

## Observed impact
A caller who is allowed to start an action can make the server run a command of their
choosing, rather than only the command the operator configured. One concrete trigger:
the caller's identity, as presented by the identity layer, carries shell
metacharacters in a field the action includes in its command (for example the caller's
login name); starting the action then executes the injected fragment with the
server's privileges.

## Security properties that must hold
- No value that describes *who the caller is* — their login name, their group
  membership, or any other attribute supplied by the identity layer — may change the
  command that runs or the environment it runs in. Such a value may appear only as
  inert text that the command receives, never as executable syntax.
- No request-supplied input that the action has not declared may reach the command or
  its environment. Only the arguments an action explicitly defines, together with
  OliveTin's own internal values, are passed through; a caller may not smuggle in an
  extra named value, whatever name they give it.
- These properties hold for every way an action can be started and for every command
  an action carries, whether that command is run through a shell or launched directly,
  and for a command's environment as much as for the command text itself.

## Contracts the fix must honour
- **Refusal.** When an incoming value would otherwise violate the above, the action
  must not run: it fails with an error and leaves no side effect (no partially executed
  command). The exact error form is unimportant.
- **Keep working.** Everything legitimate must behave exactly as today: declared
  arguments are substituted as before; the internal values OliveTin makes available to
  actions (the caller's name and the execution identifier) are still delivered, both
  into the command and into its environment; and ordinary identities keep working —
  including email-style names containing `@` and `+`. For example, a caller named
  `alice@example.com` must still run actions normally, whereas a caller whose presented
  name is `alice; touch /tmp/x` or `a$(id)` must never cause anything extra to run.

The examples above are illustrations, not the full set of inputs the fix must handle.

## Constraints
Fix the underlying problem and its close variants, not just the specific example.
Keep all legitimate use working. Do not modify or add tests. Do not look up the
upstream advisory or fix. Do not special-case the example values.
