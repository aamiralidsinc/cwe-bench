<?php
use PHPUnit\Framework\TestCase;

/**
 * A client-supplied executable payload must not be relayed to another connected client.
 * The default in-memory server implementation.
 */
final class SecAutoEvalMessageTest extends TestCase
{
    protected function tearDown(): void
    {
        ServerHarness::shutdown();
    }

    /** @return array{0:object,1:FakeConnection,2:FakeConnection} */
    private function pair(): array
    {
        $server = ServerHarness::server('message');
        $victim = ServerHarness::connect($server, ServerHarness::token(['users_id' => 42, 'name' => 'Victim']));
        $attacker = ServerHarness::connect($server, ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']));
        $victim->clear();
        $attacker->clear();
        return [$server, $victim, $attacker];
    }

    public function testBrowserPayloadInMessageIsNotRelayed(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'resourceId' => $victim->resourceId,
            'msg' => ['autoEvalCodeOnHTML' => 'globalThis.__pwned=1', 'text' => 'hello'],
        ]);

        $this->assertNotEmpty($victim->sent, 'the ordinary part of the message should still be relayed');
        $this->assertFalse(
            ServerHarness::frameHasKey(ServerHarness::lastPayload($victim), 'autoEvalCodeOnHTML'),
            'a browser-supplied executable value must not reach another client'
        );
    }

    public function testBrowserPayloadInJsonCarrierIsNotRelayed(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'resourceId' => $victim->resourceId,
            'msg' => 'notice',
            'json' => ['autoEvalCodeOnHTML' => 'globalThis.__pwned=1', 'stats' => []],
        ]);

        $this->assertNotEmpty($victim->sent);
        $this->assertFalse(
            ServerHarness::frameHasKey(ServerHarness::lastPayload($victim), 'autoEvalCodeOnHTML'),
            'the payload object carried beside the text must be filtered as well'
        );
    }

    public function testBrowserPayloadAtTopLevelIsNotRelayed(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'resourceId' => $victim->resourceId,
            'autoEvalCodeOnHTML' => 'globalThis.__pwned=1',
            'text' => 'hello',
        ]);

        $this->assertNotEmpty($victim->sent);
        $this->assertFalse(
            ServerHarness::frameHasKey(ServerHarness::lastPayload($victim), 'autoEvalCodeOnHTML'),
            'a value carried outside the usual message object must be filtered too'
        );
    }

    public function testRelayedBrowserPayloadDoesNotExecuteOnRecipient(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'resourceId' => $victim->resourceId,
            'msg' => ['autoEvalCodeOnHTML' => 'globalThis.__pwned=1', 'text' => 'hello'],
        ]);

        $result = ServerHarness::client('response', ServerHarness::lastFrame($victim));
        $this->assertFalse($result['pwned'], 'the recipient browser must not run a value a client supplied');
    }

    public function testSenderClaimsDoNotBypassTheCheck(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'resourceId' => $victim->resourceId,
            'isCommandLine' => true,
            'sentFrom' => 'php',
            'msg' => [
                'isCommandLineInterface' => true,
                'autoEvalCodeOnHTML' => 'globalThis.__pwned=1',
                'text' => 'hello',
            ],
        ]);

        $this->assertNotEmpty($victim->sent);
        $this->assertFalse(
            ServerHarness::frameHasKey(ServerHarness::lastPayload($victim), 'autoEvalCodeOnHTML'),
            'a claim written inside the frame must not change how the frame is treated'
        );
    }

    public function testEveryTargetedRecipientIsProtected(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'to_users_id' => 42,
            'msg' => ['autoEvalCodeOnHTML' => 'globalThis.__pwned=1', 'text' => 'hello'],
        ]);

        $this->assertNotEmpty($victim->sent);
        $this->assertFalse(
            ServerHarness::frameHasKey(ServerHarness::lastPayload($victim), 'autoEvalCodeOnHTML'),
            'delivery by account must be filtered like delivery by connection'
        );
    }
}
