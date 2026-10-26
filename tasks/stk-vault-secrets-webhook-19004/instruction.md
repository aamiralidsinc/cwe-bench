# A workload object can send the webhook's Vault traffic somewhere else

The Vault Secrets Webhook is a Kubernetes admission webhook. It watches Pods, Secrets and ConfigMaps, and for any value that references Vault it reads that value from Vault itself, logging in with a credential it obtains for the service account named in the object. Tenants annotate their own objects, and the webhook takes those annotations at face value.

## Impact

A tenant who can create an annotated object can choose the Vault address the webhook itself connects to. The webhook uses that address without question: it sends its Vault login there, presenting the credential it obtained for the object's service account, and then reads the object's values from whatever answers. The tenant therefore decides where the webhook's Vault traffic and that credential go.

For example, a ConfigMap in a tenant namespace annotated with `vault.security.banzaicloud.io/vault-addr: http://127.0.0.1:9000` and holding one value sourced from Vault makes the webhook send its Vault login to `127.0.0.1:9000`, and the value it injects is whatever that endpoint returns.

## The property

The webhook's own Vault connection goes only to the address the operator configured. No value supplied with a workload object may change the address the webhook connects to, and a request that asks for any other address is refused.

A workload object must also never be able to weaken the certificate verification that the webhook itself applies. An object-supplied verification setting may take effect only to the extent the operator has already allowed it; otherwise the operator's own setting governs.

## Contracts

- A request that is refused produces a client error and has no other effect: nothing is created, changed, or contacted.
- Everything that works today keeps working exactly as today.
- Fix the problem and its close variants.
- Do not look up the upstream fix or any existing implementation of it.
- Do not special-case the example.
- There is no network access.
