# Jupyter Notebook: redirects that can leave the server

Jupyter Notebook is a web application for running and sharing notebooks. Users reach it in a
browser, sign in through its login page, and are then sent on to the page they asked for. The
server also answers some requests with a redirect.

## What goes wrong

A crafted link to the login page can carry a post-sign-in destination that looks like an ordinary
path on the server but that a browser resolves as an address on another site. The user signs in
normally, and the browser then leaves the server and loads the other site.

## Required property

Every redirect the server sends must keep the user on this server: its destination, as a browser
resolves it, must not name a different host. The login flow may name another origin only when that
exact origin is one the operator has configured as allowed.

A destination that is not accepted must not be honoured: the client either receives a client error
or is sent to a safe location on this server.

This is an invariant about the destination of every redirect, not a list of cases. The example
above is one example.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
