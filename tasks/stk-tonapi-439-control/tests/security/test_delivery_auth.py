"""A delivery must carry the secret issued for the route it targets (reported route only)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))

from fakes import FakeClient, account_tx_data, delivery_refused  # noqa: E402

from pytonapi.webhook import TonapiWebhookDispatcher  # noqa: E402


def run(scenario) -> None:
    asyncio.run(scenario())


async def accepted_with_an_issued_secret(dispatcher, client, path, data, calls) -> bool:
    for endpoint in dict.fromkeys(client.ensured):
        calls.clear()
        if not await delivery_refused(
            dispatcher.process(path, data, authorization="Bearer " + FakeClient.token_for(endpoint))
        ):
            return True
    return False


def _dispatcher_with_route(url: str, route: str):
    client = FakeClient()
    dispatcher = TonapiWebhookDispatcher(url, client=client, accounts=["0:victim"])
    calls: list = []

    @dispatcher.account_tx("0:victim", path=route)
    async def handler(event) -> None:
        calls.append(event)

    return client, dispatcher, calls


def test_custom_route_needs_an_authorization_header() -> None:
    async def scenario() -> None:
        client, dispatcher, calls = _dispatcher_with_route("https://victim.example/hook", "/hook/a")
        await dispatcher.setup()
        data = account_tx_data("0:victim")

        assert await delivery_refused(dispatcher.process("/hook/a", data)), (
            "a delivery with no Authorization header was accepted"
        )
        assert calls == [], "a handler ran for a delivery with no secret"

        assert await accepted_with_an_issued_secret(dispatcher, client, "/hook/a", data, calls), (
            "the route's own issued secret was not accepted"
        )
        assert len(calls) == 1

    run(scenario)


def test_custom_route_needs_the_right_secret() -> None:
    async def scenario() -> None:
        client, dispatcher, calls = _dispatcher_with_route("https://victim.example/hook", "/hook/b")
        await dispatcher.setup()
        data = account_tx_data("0:victim")

        assert await delivery_refused(
            dispatcher.process("/hook/b", data, authorization="Bearer wrong")
        ), "a delivery with a wrong secret was accepted"
        assert calls == [], "a handler ran for a delivery with a wrong secret"

        assert await accepted_with_an_issued_secret(dispatcher, client, "/hook/b", data, calls), (
            "the route's own issued secret was not accepted"
        )
        assert len(calls) == 1

    run(scenario)


def test_custom_route_needs_the_whole_secret() -> None:
    async def scenario() -> None:
        client, dispatcher, calls = _dispatcher_with_route("https://victim.example/hook", "/hook/c")
        await dispatcher.setup()
        data = account_tx_data("0:victim")
        issued = [FakeClient.token_for(endpoint) for endpoint in dict.fromkeys(client.ensured)]
        assert issued, "no secret was issued for the registered route"

        for secret in issued:
            assert await delivery_refused(
                dispatcher.process("/hook/c", data, authorization="Bearer " + secret + " trailing")
            ), "a header that merely contains the secret was accepted"
        assert calls == [], "a handler ran for a malformed credential"

    run(scenario)


def test_custom_route_on_a_prefixed_url() -> None:
    async def scenario() -> None:
        client, dispatcher, calls = _dispatcher_with_route(
            "https://victim.example/hook", "/hook/d"
        )
        await dispatcher.setup()
        data = account_tx_data("0:victim")

        assert await delivery_refused(dispatcher.process("/hook/d", data)), (
            "a delivery with no Authorization header was accepted"
        )
        assert calls == [], "a handler ran for a delivery with no secret"

        assert await accepted_with_an_issued_secret(dispatcher, client, "/hook/d", data, calls), (
            "the route's own issued secret was not accepted"
        )
        assert len(calls) == 1

    run(scenario)
