"use strict";

const { makeSuite } = require("../support/harness");

describe("referenced message content", function () {
    const h = makeSuite();

    beforeEach(async () => { await h.start(); });
    afterEach(async () => { await h.stop(); });

    it("withholds a cached source the replier joined after", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ATK.nick);
        await h.message(h.ORIG, "the launch code is SECRET_ONE indeed", target, Date.now() - 600000);
        await h.pause(40);
        await h.join(h.ATK, Date.now());
        await h.relay(h.reply(h.ATK, target, Date.now()));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_ONE");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("withholds a fetched source the replier joined after", async () => {
        const target = h.nextId("orig");
        h.stubFetchedEvent({
            room_id: h.roomId,
            event_id: target,
            sender: h.ORIG.id,
            content: { body: "the launch code is SECRET_TWO indeed", msgtype: "m.text" },
            origin_server_ts: Date.now() - 600000,
        });
        const said = h.saysFor(h.ATK.nick);
        await h.join(h.ATK, Date.now());
        await h.relay(h.reply(h.ATK, target, Date.now()));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_TWO");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("withholds a source when the arrival time is fabricated", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ATK.nick);
        await h.message(h.ORIG, "the launch code is SECRET_THREE indeed", target, Date.now() - 600000);
        await h.pause(40);
        // The homeserver claims this member has been here since the beginning of time.
        await h.join(h.ATK, 1);
        await h.relay(h.reply(h.ATK, target, Date.now()));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_THREE");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("withholds a cached source dated after the replier joined", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ATK.nick);
        // The homeserver dates this message well into the future.
        await h.message(h.ORIG, "the launch code is SECRET_FOUR indeed", target, Date.now() + 3600000);
        await h.pause(40);
        await h.join(h.ATK, Date.now());
        await h.relay(h.reply(h.ATK, target, Date.now() + 7200000));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_FOUR");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("withholds a fetched source dated after the replier joined", async () => {
        const target = h.nextId("orig");
        h.stubFetchedEvent({
            room_id: h.roomId,
            event_id: target,
            sender: h.ORIG.id,
            content: { body: "the launch code is SECRET_FIVE indeed", msgtype: "m.text" },
            origin_server_ts: Date.now() + 3600000,
        });
        const said = h.saysFor(h.ATK.nick);
        await h.relay(h.reply(h.ATK, target, Date.now() + 7200000));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_FIVE");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("withholds a fetched source that belongs to another room", async () => {
        const target = h.nextId("orig");
        h.stubFetchedEvent({
            room_id: "!elsewhere:bar",
            event_id: target,
            sender: h.ORIG.id,
            content: { body: "the launch code is SECRET_SIX indeed", msgtype: "m.text" },
            origin_server_ts: Date.now() + 1000,
        });
        const said = h.saysFor(h.ATK.nick);
        await h.relay(h.reply(h.ATK, target, Date.now() + 400000));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_SIX");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("withholds a fetched source whose room is not stated", async () => {
        const target = h.nextId("orig");
        h.stubFetchedEvent({
            event_id: target,
            sender: h.ORIG.id,
            content: { body: "the launch code is SECRET_SEVEN indeed", msgtype: "m.text" },
            origin_server_ts: Date.now() + 1000,
        });
        const said = h.saysFor(h.ATK.nick);
        await h.relay(h.reply(h.ATK, target, Date.now() + 400000));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_SEVEN");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("withholds original words from an edit the editor joined after", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ATK.nick);
        await h.message(h.ORIG, "the secret word is SECRET_EIGHT indeed", target, Date.now() - 600000);
        await h.pause(40);
        await h.join(h.ATK, Date.now());
        h.stubEditParentAnswer(h.ATK.id);
        await h.relay(h.edit(h.ATK, target, "the secret word is REDPANDA indeed", Date.now()));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_EIGHT");
        expect(said.join("\n")).toContain("REDPANDA");
    });
});
