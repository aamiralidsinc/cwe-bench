# Stored form definitions are executable configuration

## The system

TYPO3 CMS keeps form definitions in storage. A stored definition is executable configuration that the frontend runs when a visitor submits that form. Configuration the definition carries can reach the database when the form is submitted. A definition is stored only after the framework has validated and authorised it.

## What was observed

A back end user without access to the form modules can cause a definition they were never allowed to configure to become a normal, listable, executable stored form.

## Security property that must hold

- The set of stored form definitions, the content of each one, and whether each one counts as present or removed, change only through the form framework's own persistence path, after that path has validated and authorised the exact definition being stored. No other operation may bring a definition into the stored set, alter one, take one out, or make a removed one count as present again — whatever it is called, whichever values it carries, and whoever invokes it.
- An operation that would do so is refused with no side effect: every stored definition, its content and its stored state stay exactly as they were, and the refusal is surfaced through the invoking operation's own normal error result. A refusal must not surface as an unhandled error or a crash.
- An operation the product itself performs counts as legitimate only when it goes through that persistence path. Everything that does go through it keeps working exactly as today, for every operation the product performs on stored definitions, including reversing any removal that the framework's own path performed.
- A stored definition may contain any configuration the form setup allows.
- Existing forms keep rendering and being submitted, and every existing way of managing stored definitions that goes through the framework's path keeps saving changes. Public interfaces, names and options stay as they are.

The examples above are examples, not the full set of the cases the property covers.

## Constraints

- Fix the problem and its close variants, not just the example.
- Keep every legitimate use working.
- There is no network access.
- Do not look up the upstream fix or the advisory.
- Do not special-case the example or any value used in it.
