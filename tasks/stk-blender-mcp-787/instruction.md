# Asset downloads can write files outside their temporary folder

Blender MCP connects an MCP client (an AI assistant) to Blender. The client asks the Blender
add-on to fetch and import 3D assets from hosted services. For each operation the add-on puts
the downloaded files in a temporary place of its own choosing and then hands the model to
Blender.

## Observed impact

A Poly Haven model request downloads the model and every file attached to it. When the service
response names an attached file with a path that climbs out of the folder the add-on created
for the download, the add-on writes that file wherever the path points — for example into the
user's home directory — and the model still imports as usual.

## Required behaviour

**A value the add-on did not itself choose must never cause anything to be created, written or
replaced outside the temporary area the add-on uses for that asset operation.**

This holds for every asset operation the add-on performs.

Everything that works today keeps working exactly as today.

The example above is one way to reach the problem, not the full set of paths or forms.

## Contracts

- A call that cannot be completed safely reports an error and leaves nothing behind.
- Legitimate use is unchanged: the same requests still download the same files, still import
  the same models, and still report the same results.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the
upstream fix. Do not special-case the example.
