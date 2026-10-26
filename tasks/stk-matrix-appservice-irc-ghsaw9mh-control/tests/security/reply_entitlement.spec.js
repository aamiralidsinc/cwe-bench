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
        await h.join(h.ATK, 1);
        await h.relay(h.reply(h.ATK, target, Date.now()));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_THREE");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("withholds a cached source dated after the replier joined", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ATK.nick);
        await h.message(h.ORIG, "the launch code is SECRET_FOUR indeed", target, Date.now() + 3600000);
        await h.pause(40);
        await h.join(h.ATK, Date.now());
        await h.relay(h.reply(h.ATK, target, Date.now() + 7200000));
        expect(said.length).toBeGreaterThan(0);
        expect(said.join("\n")).not.toContain("SECRET_FOUR");
        expect(said.join("\n")).toContain("Reply text");
    });
});
