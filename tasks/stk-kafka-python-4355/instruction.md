# Bound the resources a broker response can demand

`kafka-python` is a pure-Python client library for Apache Kafka. Applications use it to
connect to brokers, authenticate, and read the records that brokers return. Everything the
library receives comes from a remote peer.

## Impact

An application that connects to a broker with SASL authentication hangs before the connection
completes when the broker answers the authentication challenge with an extreme repetition
count: the client keeps re-running a key-derivation step and never returns to the caller.

## Security property

Whatever a broker — or anything else answering as one — sends, the client must not let the
response make it allocate memory or spend CPU work beyond a fixed, reasonable bound. A
response that would exceed the bound must be refused with a client error before the memory is
allocated or the work is done, and must leave no partially decoded result.

## Contracts

- Refusal: the library raises an explicit client error. The caller receives no partially
  decoded result, and nothing is silently truncated or dropped.
- Everything that works today keeps working exactly as it does today, at the same speed and
  with the same results.
- A legitimate input of the same kind as a refused one is still accepted. The example above is
  an example, not the complete set of places this property applies.
- Choose bounds that are comfortable for real deployments and that still stop exhaustion. Do
  not make a legitimate input fail because it is close to the limit.

## Constraints

- Fix the problem and its close variants.
- Keep the library's public behaviour, documented defaults and existing limits intact.
- Do not look up the upstream fix, and do not special-case the example.
