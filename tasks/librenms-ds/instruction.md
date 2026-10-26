# LibreNMS: device-supplied values shown by the web UI

LibreNMS is a network monitoring system. It polls switches, routers, servers and other devices over
SNMP, receives their syslog messages, keeps alert history, and renders device pages for operators in
the web interface. Almost everything shown on those pages originates from the monitored devices
themselves: interface, storage, sensor, processor, process, routing and inventory names and
descriptions, log fields, and the details recorded when an alert fires.

## Reported problem

A monitored device can get markup into an operator's browser session. When a device sends a log
message whose program field contains a crafted tag, the device overview page renders that tag as
HTML in its recent-syslog panel instead of showing it as text. The same happens to other names and
descriptions the device reports, and to values the system recorded from a device earlier and
displays again later.

## What must hold

No value that a monitored device supplies, or that the monitoring system records from it, may become
markup or code in a page. Wherever such a value is displayed — as element content, as an attribute
value, or inside an inline event-handler script — it must stay inert text: it must not create an
element, execute script, or break out of the surrounding code. This holds on every page that shows
device data, including values recorded earlier and displayed later.

## Contracts

- A page that displays such a value must still render normally (no error page), and the value must
  still be visible as text. Do not hide it or drop it.
- Everything that works today keeps working exactly as today: links stay links, line breaks and
  hover tooltips stay, and a legitimate value containing `&`, `'` or parentheses is displayed once,
  not double-encoded.
- The invariant above is the requirement. The trigger described in "Reported problem" is one
  example, not the list of places that need attention.

## Constraints

Fix the reported problem and its close variants while keeping legitimate use working. Do not look
up the upstream fix or advisory. Do not special-case the example.
