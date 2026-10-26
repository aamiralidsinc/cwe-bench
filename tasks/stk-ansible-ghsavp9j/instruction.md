# Ansible vault working copies

Ansible is an automation tool. `ansible-vault edit FILE` opens the decrypted contents of an encrypted file in the user's editor, then encrypts the result and writes it back.

## Impact

On a machine shared by several users, run `ansible-vault edit secrets.yml`. While the editor is open, another local user can read the decrypted contents from the working copy the command created; that user can also replace the working copy with one of their own, and can recover the plaintext after the command has returned.

## Property

Decrypted vault content must never be exposed to another local user: no other local user may be able to read that content, alter it, replace it, or recover it, and no copy of it may remain once it is no longer needed.

## Contracts

- If the operation cannot complete safely, it must fail with a clean error and leave no decrypted content behind.
- Everything that works today keeps working exactly as today.

These examples illustrate the problem; they are not the full set of affected paths.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix. Do not special-case the example.
