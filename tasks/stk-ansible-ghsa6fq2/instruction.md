# Ansible: a password given to the command line must never become a template

## What this is

Ansible is a configuration-management tool. Its command-line tools obtain the password used to
authenticate to a managed host and make it available to the run, where the connection uses it. The
user can be asked for the password at a prompt.

## What was observed

With the connection password supplied as the text `{{ 1 + 2 }}`, a run that should simply see the
literal password instead sees `3`:

```
ansible localhost -m debug -a 'msg={{ ansible_password }}' -k
```

The password was interpreted as a template expression. Any password that contains template syntax
is affected, so part of the secret can be replaced or exposed instead of being used as typed.

## What must hold

A password used to authenticate to a managed host must reach the run as literal text. Template
syntax in it must never be evaluated, whatever the password contains, and the secret must not be
replaced or exposed by expansion. A password that contains template syntax must be accepted and
used as the password; it must not be rejected and must not crash the run.

Everything that works today keeps working.

These examples are examples, not the full set. Fix the problem and its close variants; keep
legitimate use working; do not look up the upstream fix; do not special-case these examples.
