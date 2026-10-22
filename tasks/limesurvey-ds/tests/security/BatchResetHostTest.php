<?php

namespace LsBench\Tests\Security;

use LsBench\BenchCase;
use LsBench\Client;
use LsBench\Fixtures;

/**
 * The bulk account-reset action: an administrator resets the login data of an
 * existing account. The mail carries both an admin-panel link and a one-time
 * password link; neither host may come from the request.
 */
class BatchResetHostTest extends BenchCase
{
    public function testBulkResetEmailLinksDoNotFollowAttackerHost(): void
    {
        Fixtures::db()->exec('UPDATE lime_users SET last_forgot_email_password = NULL');

        $client = new Client();
        $client->login();
        $this->assertSame(302, $client->status, 'the administrator session could not be established');
        $this->assertStringContainsString('admin', $client->location());
        Fixtures::clearAllowedHosts();

        $client->submitForm(
            '?r=userManagement/batchSendAndResetLoginData',
            '?r=userManagement/index',
            ['sItems' => json_encode([Client::BATCH_UID])],
            'attacker.example'
        );

        $this->assertAttackBlocked($client, 'attacker.example', Client::BATCH_EMAIL);
    }
}
