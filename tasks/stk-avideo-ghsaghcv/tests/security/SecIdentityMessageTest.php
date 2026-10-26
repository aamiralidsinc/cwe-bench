<?php
use PHPUnit\Framework\TestCase;

/**
 * The identity a recipient sees for an incoming call must be the authenticated sender's, and
 * must be shown as text rather than interpreted as markup.
 */
final class SecIdentityMessageTest extends TestCase
{
    private const MARKUP = '<img src=x onerror=globalThis.__pwned=1>';

    protected function tearDown(): void
    {
        ServerHarness::shutdown();
    }

    /** @return array{0:object,1:FakeConnection,2:FakeConnection,string} */
    private function pair(): array
    {
        $server = ServerHarness::server('message');
        $token = ServerHarness::token(['users_id' => 7, 'name' => 'Attacker']);
        $victim = ServerHarness::connect($server, ServerHarness::token(['users_id' => 42, 'name' => 'Victim']));
        $attacker = ServerHarness::connect($server, $token);
        $victim->clear();
        $attacker->clear();
        return [$server, $victim, $attacker, $token];
    }

    private function assertNoMarkupShown(array $result): void
    {
        $this->assertIsString($result['heading'], 'the recipient should see a caller name');
        $this->assertStringNotContainsString('<', $result['heading'], 'a sender-supplied name must not be shown as markup');
        $this->assertStringNotContainsString('onerror', $result['heading']);
    }

    public function testSpoofedSenderAccountDoesNotChooseTheOtherName(): void
    {
        [$server, $victim, $attacker, $token] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => $token,
            'resourceId' => $victim->resourceId,
            'callback' => 'incomeCall',
            'msg' => [
                'to_users_id' => 42,
                'to_identification' => self::MARKUP,
                'from_users_id' => 42,
                'from_identification' => self::MARKUP,
                'from_socketResourceId' => $attacker->resourceId,
            ],
        ]);

        $result = ServerHarness::caller(ServerHarness::lastPayload($victim), 42);
        $this->assertNoMarkupShown($result);
    }

    public function testSenderSuppliedNameIsNotShown(): void
    {
        [$server, $victim, $attacker, $token] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => $token,
            'resourceId' => $victim->resourceId,
            'callback' => 'incomeCall',
            'msg' => [
                'to_users_id' => 42,
                'to_identification' => 'Victim',
                'from_users_id' => 7,
                'from_identification' => self::MARKUP,
                'from_socketResourceId' => $attacker->resourceId,
            ],
        ]);

        $result = ServerHarness::caller(ServerHarness::lastPayload($victim), 42);
        $this->assertNoMarkupShown($result);
    }

    public function testAnonymousSenderCannotImpersonate(): void
    {
        [$server, $victim, $attacker, $token] = $this->pair();
        ServerHarness::send($server, $attacker, [
            'webSocketToken' => ServerHarness::token(['users_id' => 0, 'name' => 'Anonymous']),
            'resourceId' => $victim->resourceId,
            'callback' => 'incomeCall',
            'msg' => [
                'to_users_id' => 42,
                'to_identification' => 'Victim',
                'from_users_id' => 0,
                'from_identification' => 'Victim',
                'from_socketResourceId' => $attacker->resourceId,
            ],
        ]);

        $result = ServerHarness::caller(ServerHarness::lastPayload($victim), 42);
        $this->assertNotSame(
            'Victim',
            $result['heading'],
            'an unauthenticated sender must not be shown as the account they claim'
        );
    }
}
