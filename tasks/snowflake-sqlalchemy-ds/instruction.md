# Report: compiled SQL can be restructured by application-supplied values

This project is a SQLAlchemy dialect for Snowflake. Applications build SQLAlchemy statements and
the dialect renders them as Snowflake SQL text. Applications routinely pass values that originate
outside the program, and those values end up in the compiled statement.

**Observed impact.** An application compiles a statement that names input files and takes one name
from a user upload. When the uploaded name contains a backslash immediately followed by a single
quote, the compiled statement no longer ends the file-name literal where the supplied value ends:
the remainder of the uploaded name is compiled as statement text. The same class of problem applies
wherever a supplied value reaches the compiled SQL.

**Required behaviour.** No value supplied by the application may change the structure of a compiled
statement. A value used as a name must be emitted as identifier text, with each part quoted when
that part is not a plain identifier. A value used as data must be emitted as exactly one string
literal whose decoded content is the supplied value. This holds for every value the dialect renders,
regardless of which construct carries it or how it reaches the compiler. The statement must still
compile: unsafe values are rendered inert, not refused with an error.

**Preservation.** Everything that works today keeps working exactly as today: plain names stay
unquoted (including the spelling the service folds), option values that use the service's escape
sequences keep their current spelling, values the API accepts as pre-built SQL expressions pass
through unchanged, and compilation stays deterministic with unchanged option ordering.

The example above is one illustration, not the full set of affected places or value kinds. There is
no network access.

Fix the problem and its close variants; keep legitimate use working; do not look up the upstream fix
or an existing implementation; do not special-case the example.
