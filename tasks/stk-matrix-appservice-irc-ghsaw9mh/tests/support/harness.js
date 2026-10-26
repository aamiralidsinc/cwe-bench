"use strict";

/*
 * Shared setup for the hidden suites. It drives the bridge through the project's own test
 * harness: the real AppService event dispatch, its mock homeserver (matrix-bot-sdk client)
 * and its mock IRC clients. Expected values in the suites are literals; nothing here derives
 * them from the code under test.
 */

const WORKSPACE = process.env.PRODUCT_ROOT || "/workspace";
const envBundle = require(`${WORKSPACE}/spec/util/env-bundle`);

const ORIG = { id: "@flibble:wibble", nick: "M-flibble" };
const ATK = { id: "@mallory:bar.com", nick: "M-mallory" };
const GHOST = "@irc.example_WibbleWob:some.home.server";

function makeSuite() {
    const { env, config, roomMapping, test } = envBundle();
    jasmine.DEFAULT_TIMEOUT_INTERVAL = 30000;

    const server = roomMapping.server;
    const channel = roomMapping.channel;
    const roomId = roomMapping.roomId;
    const botId = config._botUserId;
    let counter = 0;

    function nextId(prefix) {
        counter += 1;
        return `$${prefix}${counter}:bar.com`;
    }

    async function start() {
        await test.beforeEach(env);
        [ORIG, ATK].forEach((u) => {
            env.ircMock._autoConnectNetworks(server, u.nick, server);
            env.ircMock._autoJoinChannels(server, u.nick, channel);
        });
        env.ircMock._autoConnectNetworks(server, roomMapping.botNick, server);
        env.ircMock._autoJoinChannels(server, roomMapping.botNick, channel);
        await test.initEnv(env);
    }

    async function stop() {
        await test.afterEach(env);
    }

    function pause(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    function saysFor(nick) {
        const recorded = [];
        env.ircMock._whenClient(server, nick, "say", (_client, _channel, text) => {
            recorded.push(String(text));
        });
        return recorded;
    }

    function botClient() {
        return env.clientMock._client(botId);
    }

    function stubFetchedEvent(event) {
        botClient().getEvent.and.callFake(async () => event);
    }

    /*
     * The bridge library asks the homeserver who wrote the event an edit refers to and drops
     * the edit when the answer does not name the editor. A homeserver that is willing to lie
     * can answer with the editor's own id, so that the edit reaches the bridge itself.
     */
    function stubEditParentAnswer(forgedParentSender) {
        botClient().getEvent.and.callFake(async (roomIdIn, eventIdIn) => ({
            room_id: roomIdIn,
            event_id: eventIdIn,
            sender: forgedParentSender,
            content: { body: "referenced message placeholder", msgtype: "m.text" },
            origin_server_ts: 1,
        }));
    }

    function join(user, originServerTs) {
        return env.mockAppService._trigger("type:m.room.member", {
            content: { membership: "join" },
            user_id: user.id,
            state_key: user.id,
            room_id: roomId,
            origin_server_ts: originServerTs,
            type: "m.room.member",
        });
    }

    function leave(user) {
        return env.mockAppService._trigger("type:m.room.member", {
            content: { membership: "leave" },
            user_id: user.id,
            state_key: user.id,
            room_id: roomId,
            type: "m.room.member",
        });
    }

    function message(sender, body, eventId, originServerTs, extraContent) {
        return env.mockAppService._trigger("type:m.room.message", {
            content: Object.assign({ body, msgtype: "m.text" }, extraContent || {}),
            sender: sender.id,
            room_id: roomId,
            event_id: eventId,
            origin_server_ts: originServerTs,
            type: "m.room.message",
        });
    }

    /* Relay and swallow a transport rejection: a dropped message is recorded as no IRC line. */
    async function relay(promise) {
        try {
            await promise;
        }
        catch (_err) {
            // nothing to record; the assertions below decide whether that is acceptable
        }
    }

    function reply(sender, targetEventId, originServerTs) {
        return message(sender, "> <@somebody:bar.com> quoted fallback\n\nReply text", nextId("reply"),
            originServerTs, {
                "m.relates_to": { "m.in_reply_to": { event_id: targetEventId } },
            });
    }

    function edit(sender, targetEventId, newBody, originServerTs) {
        return message(sender, newBody, nextId("edit"), originServerTs, {
            "m.relates_to": { rel_type: "m.replace", event_id: targetEventId },
            "m.new_content": { body: newBody, msgtype: "m.text" },
        });
    }

    return {
        env, config, roomMapping, test,
        ORIG, ATK, GHOST, server, channel, roomId,
        start, stop, pause, saysFor, stubFetchedEvent, stubEditParentAnswer,
        join, leave, message, relay, reply, edit, nextId,
    };
}

module.exports = { makeSuite, ORIG, ATK, GHOST };
