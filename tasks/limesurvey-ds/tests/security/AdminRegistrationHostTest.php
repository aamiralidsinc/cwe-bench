<?php

namespace LsBench\Tests\Security;

use LsBench\BenchCase;
use LsBench\Client;
use LsBench\Fixtures;

/**
 * A second entry point to the account-email path: an authenticated
 * administrator creates a new account without setting a password, so the
 * application sends the new user a link to choose one.
 */
class AdminRegistrationHostTest extends BenchCase
{
    private string $username = '';
    private string $email = '';

    protected function setUp(): void
    {
        parent::setUp();
        $suffix = bin2hex(random_bytes(5));
        $this->username = 'sec_reg_' . $suffix;
        $this->email = 'sec_reg_' . $suffix . '@example.test';
    }

    protected function tearDown(): void
    {
        Fixtures::deleteUserByName($this->username);
        parent::tearDown();
    }

    public function testNewUserEmailLinkDoesNotFollowAttackerHost(): void
    {
        $client = new Client();
        $client->login();
        $this->assertSame(302, $client->status, 'the administrator session could not be established');
        $this->assertStringContainsString('admin', $client->location());
        Fixtures::clearAllowedHosts();

        $client->submitForm(
            '?r=userManagement/applyEdit',
            '?r=userManagement/index',
            [
                'User' => [
                    'users_name' => $this->username,
                    'email' => $this->email,
                    'full_name' => 'Security Registration',
                ],
                'preset_password' => '0',
                'password_repeat' => '',
            ],
            'attacker.example'
        );

        $this->assertAttackBlocked($client, 'attacker.example', $this->email);
    }
}
