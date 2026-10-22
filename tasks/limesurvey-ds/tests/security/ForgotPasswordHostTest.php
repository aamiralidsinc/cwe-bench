<?php

namespace LsBench\Tests\Security;

use LsBench\BenchCase;
use LsBench\Client;
use LsBench\Fixtures;

/**
 * The reported entry point: the unauthenticated password-reminder form.
 * No request-supplied host may become the host of the link in the email.
 */
class ForgotPasswordHostTest extends BenchCase
{
    private function sendReminderWithHost(string $attackHost): Client
    {
        Fixtures::clearForgotPasswordState();
        $client = new Client();
        $client->submitForm(
            '?r=admin/authentication/sa/forgotpassword',
            '?r=admin/authentication/sa/forgotpassword',
            [
                'user' => Client::ADMIN_USER,
                'email' => Client::ADMIN_EMAIL,
                'action' => 'forgotpass',
            ],
            $attackHost
        );
        return $client;
    }

    public function testEmailLinkDoesNotFollowPlainAttackerHost(): void
    {
        $client = $this->sendReminderWithHost('attacker.example');
        $this->assertAttackBlocked($client, 'attacker.example', Client::ADMIN_EMAIL);
    }

    public function testEmailLinkDoesNotFollowCaseAndPortVariant(): void
    {
        $client = $this->sendReminderWithHost('ATTACKER.EXAMPLE:8443');
        $this->assertAttackBlocked($client, 'ATTACKER.EXAMPLE:8443', Client::ADMIN_EMAIL);
    }

    public function testEmailLinkDoesNotFollowBracketedIpv6Variant(): void
    {
        $client = $this->sendReminderWithHost('[2001:db8::1]');
        $this->assertAttackBlocked($client, '[2001:db8::1]', Client::ADMIN_EMAIL);
    }
}
