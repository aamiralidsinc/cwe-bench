# Ansible: a value supplied as data is run as a program

Ansible is an IT automation tool. Operators describe work in playbooks, and a
play often uses values that are supplied as data from outside the playbook.

**A value supplied as data runs as a program.** A play loops over a list held
in a variable; the variable's value arrives from outside the playbook and
contains an expression. While preparing the loop the product executes that
expression, so the work in it runs with the privileges of the account running
the automation. The loop then carries on as though the value were ordinary
data.

## Required behaviour

A value supplied as data must never be executed as code: it is read only as
data, never as a program.

## Contracts

- When a value cannot be used as data, the operation fails with an error or
  the value is kept as inert text; either way, nothing in it runs.
- Everything that works today keeps working exactly as it works today,
  including a legitimate value that sits next to one that is refused.
- The example above is one example, not the full set of ways a value is used.

## Constraints

- Fix the reported problem and its close variants.
- Keep legitimate use working exactly as it works today.
- Do not look up the upstream fix.
- Do not special-case the example above.
