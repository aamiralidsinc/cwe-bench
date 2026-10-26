# October CMS: editing template content must not be a way to run PHP

October CMS is a self-hosted content management system. Editors work in a back office and author
site content as templates — pages, layouts and partials — that mix HTML with a small expression
language. An installation that does not fully trust everyone who edits templates can turn on safe
mode: with safe mode on, an editor may change the HTML and the expressions in a template, but must
not be able to run PHP on the server.

## What we saw

On an installation with safe mode on, an account that may only edit pages stored this page body:

    {% set _ = this.page.addDynamicMethod('run', 'file_put_contents') %}
    {{ this.page.run('/tmp/oct-report', 'x') }}

The next time the page was rendered, the file was written. The same account cannot save a PHP
code section — the editor refuses that — so safe mode does not deliver what it promises.

## What must be true

While safe mode is enabled, no template content that an editor can author may cause PHP code to
run. This holds for every template the application renders.

## Contracts

- A refused render or save is a plain client error (an error page, or an error raised while the
  template is processed). It must leave no side effect: nothing executed, written, created or
  changed.
- Everything that works today keeps working exactly as today.
- The example above is an example, not the full set of ways this can happen.

## Ground rules

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix or the advisory. Do not special-case the example.
