<?php
use PHPUnit\Framework\TestCase;

/**
 * The recipient browser chooses a callback by name. A name that is not an ordinary application
 * function must not turn the message into code the recipient runs.
 */
final class SecCallbackMessageTest extends TestCase
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

    public function testCallerChosenCodeIsNotExecuted(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'resourceId' => $victim->resourceId,
            'callback' => '(globalThis.__pwned=1, defaultCallback)',
            'msg' => ['text' => 'hello'],
        ]);

        $result = ServerHarness::client('message', ServerHarness::lastFrame($victim));
        $this->assertFalse($result['pwned'], 'the recipient must not run code chosen by the sender');
    }

    public function testBuiltInFunctionNameIsNotUsedAsCallback(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'resourceId' => $victim->resourceId,
            'callback' => 'setTimeout',
            'msg' => 'globalThis.__pwned=1',
        ]);

        $result = ServerHarness::client('message', ServerHarness::lastFrame($victim));
        $this->assertFalse($result['pwned'], 'a built-in name must not make the message run as code');
    }

    public function testArrayShapedFunctionNameIsNotUsedAsCallback(): void
    {
        [$server, $victim, $attacker] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']),
            'resourceId' => $victim->resourceId,
            'callback' => ['setTimeout'],
            'msg' => 'globalThis.__pwned=1',
        ]);

        $result = ServerHarness::client('message', ServerHarness::lastFrame($victim));
        $this->assertFalse($result['pwned'], 'a function name must be a plain name, not a value that stringifies to one');
    }
}
