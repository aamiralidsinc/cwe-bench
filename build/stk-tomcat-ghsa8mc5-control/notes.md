# stk-tomcat-ghsa8mc5-control — build notes

The control isolates the host effect: same pinned Apache Tomcat commit, byte-identical
instruction.md, the same real embedded-Tomcat TLS harness, but the security suite covers only the
advisory's own route (a TLS connection negotiated for one virtual host followed by an HTTP/1.1
request naming another) and the reference is the first published fix on 11.0.x (258a591b61f8) plus
its NIO2 producer follow-up (5f950a0e69).

- Security: hidden.security.ControlSniTest#requestNameSelectsAnotherVirtualHost.
- Functional: the same 10 legitimate-request tests and the project's TestSSLHostConfig.
- Checks: sf-no-fix (comment-only, the route stays served), ff-refuse-all, ff-crash,
  pass-alt-adapter (one unconditional adapter check), pass-hardening, blind (written later).
- The instruction is copied byte-for-byte from the stacked task (rule 13).
