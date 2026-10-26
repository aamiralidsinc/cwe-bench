# Protected servlets can still be reached

Apache Tomcat is a Java servlet container. An application deploys servlets, declares access rules for protected resources, and the container decides for every HTTP request whether the servlet it reaches may run.

## Observed impact

An application that registers a servlet while it starts up and declares the access rules on the servlet itself, instead of listing them in the deployment descriptor, still serves that servlet's output to an anonymous HTTP client. The request is executed even though the application declared that it must be denied.

## What must hold

Every servlet must enforce the access rules declared for it on **every request that reaches it**, however the servlet was registered and whatever path the request used. A request that does not satisfy those rules must not run the servlet's code, and must be refused.

- A refused request gets a client error (a 4xx response), and the servlet produces no output.
- Everything that works today keeps working: requests that satisfy the declared rules continue to reach the servlet exactly as they do today, and so does every application behaviour that is not an access-control decision.
- The example above is one example, not the whole set. Fix the problem and its close variants wherever a request can reach a servlet.

Do not look up the upstream fix. Do not special-case the example.
