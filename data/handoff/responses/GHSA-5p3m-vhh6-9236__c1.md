<instruction_md>
# Webhook subscription kept a cloud-metadata address

## What we observed

A caller with a normal API key sent POST /v1/subscriptions to watch the local scope. The body used on_change webhook and a delivery address of http://169.254.169.254/latest/meta-data/. The call succeeded, and the saved subscription still showed that address. The same call with a loopback address also succeeded and was saved.

Another webhook used plain http on a public host. That subscription was saved too, and when a matching memory was written the node posted the event body to that cleartext address.

On a further webhook the hostname looked public at the moment it was checked, then the notification socket opened on a link-local address and the event body was posted there.

## Impact

Saving those addresses lets this node place a request toward the cloud metadata service, the loopback interface, or a private network, and cleartext http puts the event body on the wire. A webhook address has to be refused when the subscription is saved if it is cleartext, or if it names loopback, a private range, link-local, or the instance metadata service. A notification that is already queued must not be posted to such an address either. When a hostname is used, the connection has to stay on an address that was found to be public for that connection; it must not follow a later answer that points at an internal address.

## What must keep working

Creating a webhook subscription whose address is https and names a public host, and posting the change notification to that same public host, must keep working. A wake subscription whose address is an identity URI such as stigmem://test/agent/alice rather than a web URL must still be accepted and must not be treated as a fetch. Sending the same legitimate https webhook again, with or without the same idempotency key, must return the subscription that was already saved. Listing and deleting those subscriptions must keep working.
</instruction_md>
<task_metadata_json>
{
  "entry_point": "HTTP POST /v1/subscriptions with on_change webhook stores a delivery address; a later notification posts that stored address.",
  "techniques": [
    1,
    2,
    3,
    5,
    9
  ],
  "trap": {
    "paths": [
      "node/src/stigmem_node/subscription_delivery.py",
      "node/src/stigmem_node/utility/net_util.py"
    ],
    "contract": "An https webhook to a public host is still created and the notification is posted to that public host; a wake identity URI is still accepted and is not fetched."
  },
  "fix_places": [
    "node/src/stigmem_node/routes/subscriptions.py",
    "node/src/stigmem_node/subscription_delivery.py",
    "node/src/stigmem_node/utility/net_util.py",
    "node/src/stigmem_node/settings.py"
  ],
  "unrelated_files": [
    "node/src/stigmem_node/auth.py",
    "node/src/stigmem_node/main.py",
    "node/src/stigmem_node/net_util.py"
  ],
  "test_justifications": {
    "test_security_create_metadata_address": "A webhook address has to be refused when the subscription is saved if it is cleartext, or if it names loopback, a private range, link-local, or the instance metadata service.",
    "test_security_create_loopback_https": "A webhook address has to be refused when the subscription is saved if it is cleartext, or if it names loopback, a private range, link-local, or the instance metadata service.",
    "test_security_create_private_name": "A webhook address has to be refused when the subscription is saved if it is cleartext, or if it names loopback, a private range, link-local, or the instance metadata service.",
    "test_security_create_cleartext_public": "Another webhook used plain http on a public host. That subscription was saved too, and when a matching memory was written the node posted the event body to that cleartext address.",
    "test_security_delivery_stored_cleartext": "A notification that is already queued must not be posted to such an address either.",
    "test_security_delivery_dns_rebind": "When a hostname is used, the connection has to stay on an address that was found to be public for that connection; it must not follow a later answer that points at an internal address.",
    "test_functional_https_public_ip_created": "Creating a webhook subscription whose address is https and names a public host, and posting the change notification to that same public host, must keep working.",
    "test_functional_https_public_host_posted": "Creating a webhook subscription whose address is https and names a public host, and posting the change notification to that same public host, must keep working.",
    "test_functional_wake_identity_uri": "A wake subscription whose address is an identity URI such as stigmem://test/agent/alice rather than a web URL must still be accepted and must not be treated as a fetch.",
    "test_functional_idempotent_https_webhook": "Sending the same legitimate https webhook again, with or without the same idempotency key, must return the subscription that was already saved.",
    "test_functional_list_and_delete": "Listing and deleting those subscriptions must keep working."
  }
}
</task_metadata_json>
<check_patches_json>
{
  "shallow": [
    {
      "file": "node/src/stigmem_node/routes/subscriptions.py",
      "search": "        require_garden_read(garden, identity)\n\n    # Idempotency key: return existing subscription if key matches THIS caller.",
      "replace": "        require_garden_read(garden, identity)\n\n    if req.on_change == \"webhook\":\n        from ..net_util import assert_safe_url\n        try:\n            assert_safe_url(\n                req.delivery_address,\n                allow_schemes=frozenset({\"http\", \"https\"}),\n            )\n        except ValueError as exc:\n            raise HTTPException(\n                status_code=status.HTTP_400_BAD_REQUEST,\n                detail=\"webhook address rejected\",\n            ) from exc\n\n    # Idempotency key: return existing subscription if key matches THIS caller."
    }
  ],
  "removal": [
    {
      "file": "node/src/stigmem_node/routes/subscriptions.py",
      "search": "    \"\"\"Create a subscription (Spec-X7-Subscriptions).\n\n    subscriber_identity is always the caller (BOLA).\n    \"\"\"\n    if not identity.can_read():",
      "replace": "    \"\"\"Create a subscription (Spec-X7-Subscriptions).\n\n    subscriber_identity is always the caller (BOLA).\n    \"\"\"\n    if req.on_change == \"webhook\":\n        raise HTTPException(\n            status_code=status.HTTP_400_BAD_REQUEST,\n            detail=\"webhook address rejected\",\n        )\n    if not identity.can_read():"
    }
  ],
  "alternative": [
    {
      "file": "node/src/stigmem_node/routes/subscriptions.py",
      "search": "        require_garden_read(garden, identity)\n\n    # Idempotency key: return existing subscription if key matches THIS caller.",
      "replace": "        require_garden_read(garden, identity)\n\n    if req.on_change == \"webhook\":\n        from ..net_util import assert_safe_url\n        try:\n            assert_safe_url(req.delivery_address, allow_schemes=frozenset({\"https\"}))\n        except ValueError as exc:\n            raise HTTPException(\n                status_code=status.HTTP_400_BAD_REQUEST,\n                detail=\"webhook address rejected\",\n            ) from exc\n\n    # Idempotency key: return existing subscription if key matches THIS caller."
    },
    {
      "file": "node/src/stigmem_node/subscription_delivery.py",
      "search": "    # SSRF guard (P-CONF-2): never POST to a private/loopback/link-local/IMDS\n    # address. Unsafe addresses can never become deliverable, so stop retrying.\n    try:\n        assert_safe_url(event[\"delivery_address\"], allow_schemes=frozenset({\"https\", \"http\"}))\n    except ValueError as exc:\n        logger.warning(\n            \"Webhook delivery blocked for subscription %s: unsafe delivery_address (%s)\",\n            event[\"subscription_id\"],\n            exc,\n        )\n        _mark_delivered(event[\"id\"], event[\"subscription_id\"])\n        return True\n\n    body = {\n        \"event_id\": event[\"id\"],\n        \"idempotency_key\": event[\"id\"],\n        \"subscription_id\": event[\"subscription_id\"],\n        \"event_type\": event[\"event_type\"],\n        \"fact\": sanitized,\n    }\n\n    try:\n        with httpx.Client(timeout=10.0, follow_redirects=False) as client:\n            resp = client.post(\n                event[\"delivery_address\"],\n                json=body,\n                headers={\n                    \"Content-Type\": \"application/json\",\n                    \"X-Stigmem-Event-Id\": event[\"id\"],\n                },\n            )\n\n",
      "replace": "    # Connect only to an address taken from the same lookup that was judged public.\n    # Cleartext is never posted. A later lookup must not move the socket.\n    import ipaddress\n    import socket\n    from urllib.parse import urlsplit, urlunsplit\n\n    from .net_util import _BLOCKED_NETS\n\n    address = event[\"delivery_address\"]\n    try:\n        parsed = urlsplit(address)\n        if parsed.scheme != \"https\":\n            raise ValueError(f\"disallowed scheme {parsed.scheme!r}\")\n        hostname = parsed.hostname or \"\"\n        if not hostname:\n            raise ValueError(\"missing hostname\")\n        infos = socket.getaddrinfo(hostname, None)\n        pinned = None\n        for info in infos:\n            ip = ipaddress.ip_address(info[4][0])\n            if any(ip in net for net in _BLOCKED_NETS):\n                raise ValueError(f\"blocked address {ip}\")\n            if pinned is None:\n                pinned = str(info[4][0])\n        if pinned is None:\n            raise ValueError(\"no address\")\n    except (ValueError, OSError) as exc:\n        logger.warning(\n            \"Webhook delivery blocked for subscription %s: unsafe delivery_address (%s)\",\n            event[\"subscription_id\"],\n            exc,\n        )\n        _mark_delivered(event[\"id\"], event[\"subscription_id\"])\n        return True\n\n    ip_host = f\"[{pinned}]\" if \":\" in pinned else pinned\n    if parsed.port is not None:\n        netloc = f\"{ip_host}:{parsed.port}\"\n        host_header = f\"{hostname}:{parsed.port}\"\n    else:\n        netloc = ip_host\n        host_header = hostname\n    pinned_url = urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))\n\n    body = {\n        \"event_id\": event[\"id\"],\n        \"idempotency_key\": event[\"id\"],\n        \"subscription_id\": event[\"subscription_id\"],\n        \"event_type\": event[\"event_type\"],\n        \"fact\": sanitized,\n    }\n\n    try:\n        with httpx.Client(timeout=10.0, follow_redirects=False) as client:\n            resp = client.post(\n                pinned_url,\n                json=body,\n                headers={\n                    \"Content-Type\": \"application/json\",\n                    \"X-Stigmem-Event-Id\": event[\"id\"],\n                    \"Host\": host_header,\n                },\n            )\n\n"
    }
  ]
}
</check_patches_json>
