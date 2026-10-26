# HL7 FHIR core library — a crafted health card can wedge the decoder

The HL7 FHIR core library provides the parsers and validator that applications use to read FHIR
resources, including Smart Health Cards. A Smart Health Card is a signed token whose payload is a
compressed JSON document that the library decompresses before the card can be read.

## What was observed

An application that reads an untrusted health card can stop making progress. A card whose compressed
payload segment is truncated, or otherwise stops advancing the decompressor, is accepted as input:
the decoder keeps waiting for output that will never come and never returns. Reading one such card is
enough to wedge the process that received it, holding a CPU until the process is killed.

## The property

Decompression of an untrusted health-card payload must always finish in bounded work. Whenever the
decoder cannot make further progress — the stream ends early, yields nothing, or otherwise stops
advancing — it must stop and either return what it has or report the input as invalid; it must never
repeat forever. This holds for every payload, however it reaches the decoder: no untrusted payload may
consume unbounded time or memory.

## Contracts

- A card that cannot be decoded ends the way an invalid card already ends for the caller: the decode
  returns or reports an input error. It must not crash the process, and it must never be treated as a
  valid card.
- A card whose content is legitimately large still decodes. The fault is a decode that never ends,
  not the size of the input or of the decoded result.
- Every legitimate card keeps working exactly as it does today.
- The example is an example, not the full set.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
