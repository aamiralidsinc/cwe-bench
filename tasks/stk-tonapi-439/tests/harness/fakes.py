"""Test doubles for the TONAPI webhook client.

The dispatcher talks to the TONAPI service through a client object and through
the bound webhook objects that client hands back. These doubles record every
call so a test can observe what the SDK asked the service to do.
"""

from __future__ import annotations

import types


class FakeWebhook:
    """The bound webhook object a real client returns from ``ensure()``."""

    def __init__(self, endpoint: str, token: str) -> None:
        self.endpoint = endpoint
        self.token = token
        self.subscriptions: list[tuple] = []

    async def sync_accounts(self, accounts: list) -> None:
        self.subscriptions.append(("accounts", list(accounts)))

    async def subscribe_mempool_msg(self) -> None:
        self.subscriptions.append(("mempool",))

    async def subscribe_opcode_msg(self, opcode: str) -> None:
        self.subscriptions.append(("opcode", opcode))

    async def subscribe_new_contracts(self) -> None:
        self.subscriptions.append(("new_contracts",))


class FakeClient:
    """A duck-typed webhook service: one webhook per endpoint, with a stable secret."""

    def __init__(self) -> None:
        self.ensured: list[str] = []
        self.requests: list[tuple[str, str, object]] = []
        self._webhooks: dict[str, tuple[int, FakeWebhook]] = {}
        self._next_id = 0

    @staticmethod
    def token_for(endpoint: str) -> str:
        return "issued-for:" + endpoint

    async def create_session(self) -> None:
        pass

    async def ensure(self, endpoint: str) -> FakeWebhook:
        self.ensured.append(endpoint)
        if endpoint not in self._webhooks:
            self._next_id += 1
            self._webhooks[endpoint] = (
                self._next_id,
                FakeWebhook(endpoint, self.token_for(endpoint)),
            )
        return self._webhooks[endpoint][1]

    async def list(self) -> list:
        return [
            types.SimpleNamespace(id=webhook_id, endpoint=endpoint, token=webhook.token)
            for endpoint, (webhook_id, webhook) in sorted(self._webhooks.items())
        ]

    async def request(self, method: str, path: str, body: object = None) -> None:
        self.requests.append((method, path, body))

    async def close_session(self) -> None:
        pass

    def webhook_id(self, endpoint: str) -> int:
        return self._webhooks[endpoint][0]


def account_tx_data(account_id: str = "0:abc", tx_hash: str = "deadbeef") -> dict:
    return {"event_type": "account_tx", "account_id": account_id, "lt": 100, "tx_hash": tx_hash}


def mempool_data(boc: str = "te6cc...") -> dict:
    return {"event_type": "mempool_msg", "boc": boc}


def opcode_data(account_id: str = "0:abc", tx_hash: str = "cafebabe") -> dict:
    return {"event_type": "opcode_msg", "account_id": account_id, "lt": 100, "tx_hash": tx_hash}


def new_contracts_data(account_id: str = "0:abc", tx_hash: str = "feedface") -> dict:
    return {"event_type": "new_contracts", "account_id": account_id, "lt": 100, "tx_hash": tx_hash}


async def delivery_refused(delivery) -> bool:
    """Run one delivery coroutine; True when it was refused by any raised error."""
    try:
        await delivery
    except Exception:  # noqa: BLE001 - the refusal form is any client error
        return True
    return False
