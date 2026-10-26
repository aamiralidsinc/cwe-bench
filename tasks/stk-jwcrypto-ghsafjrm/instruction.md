# Encrypted tokens that expand on decryption

This project is a Python library for JOSE encryption. Applications use it to decrypt tokens that
arrive from outside the process.

## Impact

A service that decrypts an encrypted token supplied by an unauthenticated party can be made to
consume unbounded memory and time: a token of a few kilobytes can expand into hundreds of megabytes
of plaintext during decryption.

## Property

No decryption call may produce more than the allowed amount of decompressed plaintext in total. A
token that would exceed the allowance must be refused with a client error, and no plaintext from it
may be left on the object.

Compression must not be applied to content unless the fact that the content is compressed is itself
covered by the authentication tag.

## Contracts

- The default allowance is 8 MiB (8,388,608 bytes) of decompressed plaintext per decryption call. It
  is a documented default that an operator may raise.
- A refused decryption must raise a client error and leave no plaintext behind.
- Every legitimate use keeps working exactly as today: compressed content within the allowance still
  decrypts to the original bytes, and uncompressed content is unaffected however large it is.

These examples illustrate the problem; they are not the full set of affected paths.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example.
