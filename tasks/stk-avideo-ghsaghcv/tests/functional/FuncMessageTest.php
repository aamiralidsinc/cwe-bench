<?php
use PHPUnit\Framework\TestCase;

/**
 * Legitimate traffic on the in-memory server implementation keeps working unchanged.
 */
final class FuncMessageTest extends TestCase
{
    protected function tearDown(): void
    {
        ServerHarness::shutdown();
    }

    private function pair(): array
    {
        $server = ServerHarness::server('message');
        $victim = ServerHarness::connect($server, ServerHarness::token(['users_id' => 42, 'name' => 'Victim']));
        $attacker = ServerHarness::connect($server, ServerHarness::token(['users_id' => 7, 'name' => 'Alice']));
        $victim->clear();
        $attacker->clear();
        return [$server, $victim, $attacker];
    }

    public function testOrdinaryMessageIsDeliveredIntact(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Alice']),
            'resourceId' => $victim->resourceId,
            'msg' => ['text' => 'hello world', 'meta' => ['score' => 5]],
        ]);

        $payload = ServerHarness::lastPayload($victim);
        $this->assertSame('hello world', $payload['text']);
        $this->assertSame(5, $payload['meta']['score']);
    }

    public function testDirectTargetingByConnection(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Alice']),
            'resourceId' => $victim->resourceId,
            'msg' => ['text' => 'for you'],
        ]);

        $this->assertSame('for you', ServerHarness::lastPayload($victim)['text']);
    }

    public function testDirectTargetingByAccount(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Alice']),
            'to_users_id' => 42,
            'msg' => ['text' => 'for you too'],
        ]);

        $this->assertSame('for you too', ServerHarness::lastPayload($victim)['text']);
    }

    public function testLegitimateFunctionNameIsRelayedAndRuns(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Alice']),
            'resourceId' => $victim->resourceId,
            'callback' => 'incomeCall',
            'msg' => ['text' => 'ring'],
        ]);

        $frame = ServerHarness::lastFrame($victim);
        $this->assertSame('incomeCall', $frame['callback']);
        $result = ServerHarness::client('message', $frame);
        $this->assertSame(1, $result['callbackCalls']);
    }

    /** A frame the server itself produced keeps its small UI script. */
    public function testServerGeneratedUiUpdateIsDelivered(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        $payload = ['stats' => ['n' => 1], 'autoEvalCodeOnHTML' => 'globalThis.__uiEffect="hidden"'];
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 0, 'name' => 'server', 'sentFrom' => 'php']),
            'resourceId' => $victim->resourceId,
            'callback' => 'socketRemoveLiveLinks',
            'msg' => json_encode($payload),
            'json' => $payload,
            'isCommandLine' => false,
        ]);

        $frame = ServerHarness::lastFrame($victim);
        $this->assertTrue(
            ServerHarness::frameHasKey($frame['msg'], 'autoEvalCodeOnHTML'),
            'a server-generated UI update must keep the field the client applies'
        );
        $result = ServerHarness::client('response', $frame);
        $this->assertSame('hidden', $result['uiEffect'], 'the server-generated UI update must still take effect');
    }

    public function testServerGeneratedPayloadIsNotAltered(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        $payload = ['stats' => ['n' => 2], 'autoEvalCodeOnHTML' => 'globalThis.__uiEffect="gone"'];
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 0, 'name' => 'server', 'sentFrom' => 'php']),
            'resourceId' => $victim->resourceId,
            'callback' => 'socketRemoveLiveLinks',
            'msg' => json_encode($payload),
            'json' => $payload,
        ]);

        $received = ServerHarness::lastPayload($victim);
        $this->assertSame(2, $received['stats']['n']);
        $this->assertSame($payload['autoEvalCodeOnHTML'], $received['autoEvalCodeOnHTML']);
    }

    /** An ordinary call notice still shows the authenticated caller to the recipient. */
    public function testLegitimateCallShowsAuthenticatedSenderName(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Alice']),
            'resourceId' => $victim->resourceId,
            'callback' => 'incomeCall',
            'msg' => [
                'to_users_id' => 42,
                'to_identification' => 'Victim',
                'from_users_id' => 7,
                'from_identification' => 'Alice',
                'from_socketResourceId' => $attacker->resourceId,
            ],
        ]);

        $result = ServerHarness::caller(ServerHarness::lastPayload($victim), 42);
        $this->assertSame('Alice', $result['heading'], 'a call from a signed-in visitor must show that visitor');
    }
}
