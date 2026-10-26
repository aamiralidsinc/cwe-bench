# Apache Tomcat: TLS configuration and the served virtual host

Tomcat is a Java servlet container. One TLS connector can serve several virtual hosts, and each
virtual host can have its own TLS configuration. For example, one host may require the client to
present a certificate while another does not. The TLS configuration is chosen when the connection
is established; the virtual host that handles a request is chosen from the name the request
carries.

## Observed impact

A client can establish the TLS connection under one virtual host's configuration and then send a
request that names a different virtual host, and that second host handles the request. In
particular, a connection that never presented a client certificate can still have a request named
for a host that requires client-certificate verification served by that host.

## Required property

For every request, the TLS configuration in force for the connection must be the same TLS
configuration that belongs to the virtual host the request is actually served by. When the two
differ, the request must be refused before the application runs.

## Contracts

- A refusal is a client error; the application must not run and nothing may be changed.
- Everything that works today must keep working. A request that is served under the same TLS
  configuration as its connection must continue to be served, and existing configurations and
  deployments must be unaffected.
- Request syntax and accepted values do not change.

## Notes

- The example above shows one way the problem appears; it is not the full set.
- Fix the problem and its close variants, without special-casing the example.
- Keep legitimate use working.
- Do not look up the upstream fix.
