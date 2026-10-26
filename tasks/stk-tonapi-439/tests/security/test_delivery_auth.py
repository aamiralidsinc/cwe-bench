"""A delivery must carry the secret issued for the route it targets."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))

from fakes import (  # noqa: E402
    FakeClient,
    account_tx_data,
    delivery_refused,
    mempool_data,
)

from pytonapi.webhook import TonapiWebhookDispatcher  # noqa: E402


def run(scenario) -> None:
    asyncio.run(scenario())


async def first_accepted_secret(dispatcher, client, path, data, calls) -> bool:
    """Try the secrets the service issued during setup; True if one is accepted."""
    for endpoint in dict.fromkeys(client.ensured):
        calls.clear()
        refused = await delivery_refused(
            dispatcher.process(path, data, authorization="Bearer " + FakeClient.token_for(endpoint))
        )
        if not refused:
            return True
    return False


def test_route_of_the_application_needs_its_issued_secret() -> None:
    async def scenario() -> None:
        client = FakeClient()
        dispatcher = TonapiWebhookDispatcher(
            "https://victim.example/hook", client=client, accounts=["0:victim"]
        )
        calls: list = []

        @dispatcher.account_tx("0:victim", path="/hook/custom")
        async def handler(event) -> None:
            calls.append(event)

        await dispatcher.setup()
        data = account_tx_data("0:victim")

        assert await delivery_refused(dispatcher.process("/hook/custom", data)), (
            "a delivery with no Authorization header was accepted"
        )
        assert calls == [], "a handler ran for a delivery with no secret"

        assert await delivery_refused(
            dispatcher.process("/hook/custom", data, authorization="Bearer not-the-secret")
        ), "a delivery with a wrong secret was accepted"
        assert calls == [], "a handler ran for a delivery with a wrong secret"

        assert await first_accepted_secret(dispatcher, client, "/hook/custom", data, calls), (
            "the route's own issued secret was not accepted"
        )
        assert len(calls) == 1, "a correctly signed delivery did not reach the handler"

    run(scenario)


def test_route_of_the_application_needs_the_whole_secret() -> None:
    async def scenario() -> None:
        client = FakeClient()
        dispatcher = TonapiWebhookDispatcher(
            "https://victim.example/hook", client=client, accounts=["0:victim"]
        )
        calls: list = []

        @dispatcher.account_tx("0:victim", path="/hook/custom")
        async def handler(event) -> None:
            calls.append(event)

        await dispatcher.setup()
        data = account_tx_data("0:victim")
        issued = [FakeClient.token_for(endpoint) for endpoint in dict.fromkeys(client.ensured)]
        assert issued, "no secret was issued for the registered route"

        for secret in issued:
            assert await delivery_refused(
                dispatcher.process(
                    "/hook/custom", data, authorization="Bearer " + secret + " trailing"
                )
            ), "a header that merely contains the secret was accepted"
        assert calls == [], "a handler ran for a malformed credential"

    run(scenario)


def test_route_added_after_setup_needs_a_secret() -> None:
    async def scenario() -> None:
        client = FakeClient()
        dispatcher = TonapiWebhookDispatcher("https://victim.example", client=client)
        tx_calls: list = []

        @dispatcher.account_tx()
        async def tx_handler(event) -> None:
            tx_calls.append(event)

        await dispatcher.setup()

        pool_calls: list = []
        try:

            @dispatcher.mempool_msg()
            async def pool_handler(event) -> None:
                pool_calls.append(event)

        except Exception:  # noqa: BLE001
            # Refusing to add a route that cannot be verified is also a refusal.
            return

        data = mempool_data()
        assert await delivery_refused(dispatcher.process("/mempool-msg", data)), (
            "a delivery to a route added after setup was accepted without a secret"
        )
        assert pool_calls == [], "a handler ran for a delivery with no secret"

        await dispatcher.setup()
        assert await first_accepted_secret(
            dispatcher, client, "/mempool-msg", data, pool_calls
        ), "the newly provisioned route's own secret was not accepted"
        assert len(pool_calls) == 1

    run(scenario)


def test_custom_route_added_after_setup_needs_a_secret() -> None:
    async def scenario() -> None:
        client = FakeClient()
        dispatcher = TonapiWebhookDispatcher("https://victim.example/hook", client=client)
        calls: list = []

        @dispatcher.account_tx()
        async def first_handler(event) -> None:
            calls.append(event)

        await dispatcher.setup()

        try:

            @dispatcher.account_tx(path="/hook/late")
            async def late_handler(event) -> None:
                pass

        except Exception:  # noqa: BLE001
            return

        data = account_tx_data()
        assert await delivery_refused(dispatcher.process("/hook/late", data)), (
            "a delivery to a route added after setup was accepted without a secret"
        )
        assert calls == [], "a handler ran for a delivery with no secret"

        await dispatcher.setup()
        assert await first_accepted_secret(
            dispatcher, client, "/hook/late", data, calls
        ), "the newly provisioned route's own secret was not accepted"
        assert calls, "a correctly signed delivery did not reach any handler"

    run(scenario)


def test_every_registered_route_needs_and_accepts_an_issued_secret() -> None:
    async def scenario() -> None:
        client = FakeClient()
        dispatcher = TonapiWebhookDispatcher("https://victim.example", client=client)
        calls: list = []

        @dispatcher.account_tx(path="/route-a")
        async def handler_a(event) -> None:
            calls.append("a")

        @dispatcher.account_tx(path="/route-b")
        async def handler_b(event) -> None:
            calls.append("b")

        await dispatcher.setup()
        data = account_tx_data()

        for route in ("/route-a", "/route-b"):
            assert await delivery_refused(dispatcher.process(route, data)), (
                f"a delivery to {route} was accepted without a secret"
            )
            assert calls == [], f"a handler ran for an unsigned delivery to {route}"

        for route in ("/route-a", "/route-b"):
            assert await first_accepted_secret(dispatcher, client, route, data, calls), (
                f"a delivery carrying an issued secret was not accepted on {route}"
            )
            assert calls, f"no handler ran for a correctly signed delivery to {route}"
            calls.clear()

    run(scenario)
