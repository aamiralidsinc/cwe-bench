<?php

namespace LsBench\Tests\Security;

use LsBench\BenchCase;
use LsBench\Client;

/**
 * The API interface can also ask the application to send an account its reset
 * link. It is a separate mail producer: it builds the message itself instead of
 * going through the account service or the shared mailer, so neither a service
 * fix nor a mailer fix reaches it.
 */
class ApiResetHostTest extends BenchCase
{
    private function sessionKey(Client $client): string
    {
        $client->postJson('?r=admin/remotecontrol', [
            'method' => 'get_session_key',
            'params' => [Client::ADMIN_USER, Client::ADMIN_PASS],
            'id' => 1,
        ]);
        $decoded = json_decode($client->body, true);
        $this->assertIsArray($decoded, 'the API did not answer the login call: ' . substr($client->body, 0, 200));
        $this->assertIsString($decoded['result'] ?? null, 'no API session key: ' . substr($client->body, 0, 200));
        return $decoded['result'];
    }

    public function testApiResetEmailLinkDoesNotFollowAttackerHost(): void
    {
        $client = new Client();
        $key = $this->sessionKey($client);

        $client->postJson('?r=admin/remotecontrol', [
            'method' => 'reset_user_password',
            'params' => [$key, Client::ADMIN_USER],
            'id' => 2,
        ], 'attacker.example');

        $this->assertNoMessageOrTrustedLinks($client, 'attacker.example', Client::ADMIN_EMAIL);
    }
}
