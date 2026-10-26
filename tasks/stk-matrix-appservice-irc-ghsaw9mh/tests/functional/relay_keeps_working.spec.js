"use strict";

const { makeSuite } = require("../support/harness");

describe("legitimate relay behaviour", function () {
    const h = makeSuite();

    beforeEach(async () => { await h.start(); });
    afterEach(async () => { await h.stop(); });

    it("keeps a quoted source for a member already present", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ATK.nick);
        await h.message(h.ORIG, "the launch code is ZEBRA_ONE indeed", target, Date.now());
        await h.relay(h.reply(h.ATK, target, Date.now() + 400000));
        expect(said.join("\n")).toContain("ZEBRA_ONE");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("keeps a quoted source when the member joined before the message", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ATK.nick);
        await h.join(h.ATK, Date.now());
        await h.pause(50);
        await h.message(h.ORIG, "the launch code is ZEBRA_TWO indeed", target, Date.now() + 1000);
        await h.relay(h.reply(h.ATK, target, Date.now() + 400000));
        expect(said.join("\n")).toContain("ZEBRA_TWO");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("keeps the diff for an edit by the message author", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ORIG.nick);
        await h.message(h.ORIG, "the secret word is ZEBRA_THREE indeed", target, Date.now() - 600000);
        h.stubEditParentAnswer(h.ORIG.id);
        await h.relay(h.edit(h.ORIG, target, "the secret word is REDPANDA_THREE indeed", Date.now()));
        expect(said.join("\n")).toContain("s/ZEBRA_THREE/REDPANDA_THREE/");
    });

    it("keeps a quoted source for a fetched message in the same room", async () => {
        const target = h.nextId("orig");
        h.stubFetchedEvent({
            room_id: h.roomId,
            event_id: target,
            sender: h.ORIG.id,
            content: { body: "the launch code is ZEBRA_FOUR indeed", msgtype: "m.text" },
            origin_server_ts: Date.now() + 1000,
        });
        const said = h.saysFor(h.ATK.nick);
        await h.relay(h.reply(h.ATK, target, Date.now() + 400000));
        expect(said.join("\n")).toContain("ZEBRA_FOUR");
        expect(said.join("\n")).toContain("Reply text");
    });

    it("keeps the original nick when the referred message has no usable time", async () => {
        const target = h.nextId("orig");
        h.stubFetchedEvent({
            room_id: h.roomId,
            event_id: target,
            sender: h.GHOST,
            content: { body: "This is the real message", msgtype: "m.text" },
        });
        const said = h.saysFor(h.ATK.nick);
        await h.relay(h.reply(h.ATK, target, Date.now()));
        expect(said.join("\n")).toContain("WibbleWob");
        expect(said.join("\n")).toContain("Reply text");
        expect(said.join("\n")).not.toContain("This is the real message");
    });

    it("relays the reply when the referred message cannot be fetched", async () => {
        const target = h.nextId("orig");
        const said = h.saysFor(h.ATK.nick);
        await h.relay(h.reply(h.ATK, target, Date.now()));
        expect(said.join("\n")).toContain("Reply text");
    });
});
