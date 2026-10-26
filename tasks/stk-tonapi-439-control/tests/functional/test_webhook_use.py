"""Legitimate deliveries keep working, and the documented interfaces keep their shape."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))

from fakes import (  # noqa: E402
    FakeClient,
    account_tx_data,
    delivery_refused,
    mempool_data,
    new_contracts_data,
    opcode_data,
)

from pytonapi.webhook import (  # noqa: E402
    AccountTxEvent,
    MempoolMsgEvent,
    NewContractsEvent,
    OpcodeMsgEvent,
    TonapiWebhookDispatcher,
    WebhookEventType,
)


def run(scenario) -> None:
    asyncio.run(scenario())


async def first_accepted_secret(dispatcher, client, path, data, calls) -> bool:
    for endpoint in dict.fromkeys(client.ensured):
        calls.clear()
        refused = await delivery_refused(
            dispatcher.process(path, data, authorization="Bearer " + FakeClient.token_for(endpoint))
        )
        if not refused:
            return True
    return False


def test_dispatcher_without_a_client_keeps_dispatching_unsigned() -> None:
    async def scenario() -> None:
        dispatcher = TonapiWebhookDispatcher()
        seen: dict[str, list] = {"tx": [], "pool": [], "opcode": [], "contracts": []}

        @dispatcher.account_tx()
        async def on_tx(event: AccountTxEvent) -> None:
            seen["tx"].append(event)

        @dispatcher.mempool_msg()
        async def on_pool(event: MempoolMsgEvent) -> None:
            seen["pool"].append(event)

        @dispatcher.opcode_msg()
        async def on_opcode(event: OpcodeMsgEvent) -> None:
            seen["opcode"].append(event)

        @dispatcher.new_contracts()
        async def on_contracts(event: NewContractsEvent) -> None:
            seen["contracts"].append(event)

        await dispatcher.process("/account-tx", account_tx_data())
        await dispatcher.process("/mempool-msg", mempool_data())
        await dispatcher.process("/opcode-msg", opcode_data())
        await dispatcher.process("/new-contracts", new_contracts_data())

        assert all(len(items) == 1 for items in seen.values()), seen

    run(scenario)


def test_signed_deliveries_on_ordinary_routes_keep_working() -> None:
    async def scenario() -> None:
        client = FakeClient()
        dispatcher = TonapiWebhookDispatcher(
            "https://victim.example",
            client=client,
            accounts=["0:victim"],
            opcodes=["0x7362d09c"],
        )
        tx_calls: list = []
        pool_calls: list = []

        @dispatcher.account_tx("0:victim")
        async def on_tx(event: AccountTxEvent) -> None:
            tx_calls.append(event)

        @dispatcher.mempool_msg()
        async def on_pool(event: MempoolMsgEvent) -> None:
            pool_calls.append(event)

        await dispatcher.setup()

        tx_secret = FakeClient.token_for("https://victim.example/account-tx")
        pool_secret = FakeClient.token_for("https://victim.example/mempool-msg")

        await dispatcher.process(
            "/account-tx", account_tx_data("0:victim"), authorization="Bearer " + tx_secret
        )
        assert len(tx_calls) == 1

        assert await delivery_refused(
            dispatcher.process("/account-tx", account_tx_data("0:victim"), authorization="Bearer nope")
        ), "an ordinary route accepted a wrong secret"
        assert len(tx_calls) == 1

        await dispatcher.process(
            "/mempool-msg", mempool_data(), authorization="Bearer " + pool_secret
        )
        assert len(pool_calls) == 1

    run(scenario)


def test_prefixed_public_url_keeps_routing_its_ordinary_routes() -> None:
    async def scenario() -> None:
        client = FakeClient()
        dispatcher = TonapiWebhookDispatcher(
            "https://victim.example/hook", client=client, accounts=["0:victim"]
        )
        calls: list = []

        @dispatcher.account_tx("0:victim")
        async def on_tx(event: AccountTxEvent) -> None:
            calls.append(event)

        await dispatcher.setup()
        secret = FakeClient.token_for("https://victim.example/hook/account-tx")
        await dispatcher.process(
            "/hook/account-tx", account_tx_data("0:victim"), authorization="Bearer " + secret
        )
        assert len(calls) == 1

    run(scenario)


def test_handler_fan_out_and_account_filters_keep_working() -> None:
    async def scenario() -> None:
        dispatcher = TonapiWebhookDispatcher()
        filtered: list = []
        catch_all: list = []

        @dispatcher.account_tx("0:target")
        async def on_target(event: AccountTxEvent) -> None:
            filtered.append(event)

        @dispatcher.account_tx()
        async def on_any(event: AccountTxEvent) -> None:
            catch_all.append(event)

        await dispatcher.process("/account-tx", account_tx_data("0:target"))
        await dispatcher.process("/account-tx", account_tx_data("0:other"))

        assert len(filtered) == 1
        assert len(catch_all) == 2

    run(scenario)


def test_route_listing_keeps_its_documented_shape() -> None:
    async def scenario() -> None:
        dispatcher = TonapiWebhookDispatcher()

        @dispatcher.account_tx()
        async def on_tx(event: AccountTxEvent) -> None:
            pass

        @dispatcher.mempool_msg()
        async def on_pool(event: MempoolMsgEvent) -> None:
            pass

        listing = dispatcher.paths
        assert isinstance(listing, dict), "the route listing is no longer a mapping"
        assert len(listing) == 2
        for event_type, route in listing.items():
            assert isinstance(event_type, WebhookEventType)
            assert isinstance(route, str), "a route listing value is no longer a single route"

    run(scenario)


def test_a_later_registered_route_works_after_setup_runs_again() -> None:
    async def scenario() -> None:
        client = FakeClient()
        dispatcher = TonapiWebhookDispatcher("https://victim.example", client=client)

        @dispatcher.account_tx()
        async def on_tx(event: AccountTxEvent) -> None:
            pass

        await dispatcher.setup()
        pool_calls: list = []

        try:

            @dispatcher.mempool_msg()
            async def on_pool(event: MempoolMsgEvent) -> None:
                pool_calls.append(event)

        except Exception:  # noqa: BLE001 - refusing the registration is a valid design
            return

        await dispatcher.setup()
        assert await first_accepted_secret(
            dispatcher, client, "/mempool-msg", mempool_data(), pool_calls
        ), "a route registered after the first setup never became usable"
        assert len(pool_calls) == 1

    run(scenario)
