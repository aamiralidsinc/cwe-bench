# Invalid UTF-8 is silently turned into other characters

ujson is a fast JSON encoder and decoder for Python. Applications use it to write data out as
JSON and to read JSON they receive, and they rely on the library's text being an exact
representation of the data: a value that goes through it must come back as the same code points,
and bytes that do not encode those code points must not be invented into them.

## Observed impact

A bytes value that is not valid text is accepted, silently turned into different characters, and
the call reports success. For example:

    >>> ujson.dumps(b"\xc3\x13", reject_bytes=False)
    '"\\u00d3"'

The two bytes are not an encoding of U+00D3, yet the output claims that code point, so input that
should have been rejected is quietly rewritten instead.

## Required properties

**Writing.** When the library writes data as JSON text, every byte sequence it accepts must be
represented exactly as the code points it encodes. A sequence that is not a complete encoding of
exactly one code point must be refused with an error; it must never be turned into a code point it
does not encode.

**Reading.** When the library reads data from JSON text, a byte sequence in the text that is not a
complete encoding of exactly one code point must likewise be refused with an error; it must never
be turned into a code point it does not encode.

Both are invariants, not lists of cases. The example above is one illustration.

## Contracts

- A refusal is an error raised by the call. Nothing is silently rewritten, and no substitute or
  partial value is returned.
- Everything that works today keeps working exactly as today; legitimate values, including
  non-ASCII and multi-byte text, keep round-tripping unchanged.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
