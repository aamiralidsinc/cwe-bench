# pyLoad — configuration changes reach actions they should not

pyLoad is a download manager with a web interface and a JSON API. Accounts carry permissions; the
settings permission lets an account open the settings pages and change configuration values through
the API.

## Observed problem

An account that is not an administrator but holds only the settings permission can change, through
the settings API, the program the service runs when it reconnects its network connection. The value
is stored, and the download engine executes that program later. The account never needed
administrator rights.

## Security properties

**Settings the service acts on.** Only an administrator may change a setting whose value decides
what the service executes, how it is exposed to others, or what it accepts or presents as proof of
identity. A change attempted from any other account has no effect: the stored value stays as it was.

**The service's private working area.** The data the service stores for its users must never be
stored in the area the service reserves for its own temporary work, or anywhere within it. A
configuration value that would do so does not take effect: the service keeps that data outside the
area, and nothing is created inside it.

Both are invariants, not a list of cases. The example above is one instance.

## Behaviour that must not change

Everything that works today keeps working. An account without administrator rights keeps being able
to make the changes it may make today, and an administrator can still change any setting.

## Constraints

Fix the problem and its close variants. Keep every legitimate use working. Do not look up the
upstream fix. Do not special-case the example above.
