# Field layout configuration can run code chosen by an administrator

Craft CMS is a content management system. Administrators build field layouts in the control panel, and the server turns the submitted configuration into layout objects.

## Impact

An administrator can include a key in a submitted field layout configuration that names an additional Yii behavior. Craft applies the configuration to the layout object it builds, constructs the named class, and attaches it. The class runs on the server during the request, which is remote code execution. Nothing else about the submission needs to be unusual, so the request looks like an ordinary layout save.

For example, saving a field layout through the control panel with such a configuration makes Craft construct and attach the named class while it assembles the layout.

## The property

Configuration data that the application receives from outside its own code must never cause the application to instantiate a class named in that data, or to attach a class named in that data as a Yii behavior. This is a property of the data itself: no part of it may name a class that the application then constructs.

## Contracts

- A configuration that is refused must produce a client error and have no further effect. A fatal error or a server error is not a refusal.
- Every legitimate configuration keeps working exactly as it does today.
- Fix the problem and its close variants.
- Do not look up the upstream fix or any existing implementation of it.
- Do not special-case the example.
- There is no network access.
