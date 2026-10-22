<?php

namespace LsBench\Tests\Functional;

use LsBench\BenchCase;
use LsBench\Client;
use LsBench\Fixtures;

/**
 * Account mail keeps working for ordinary traffic. Requests arrive at the
 * server's own address while the installation publishes a separate public URL;
 * both must keep working together.
 */
class AccountEmailFunctionalTest extends BenchCase
{
    public function testForgotPasswordDeliversUsableLink(): void
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
            ]
        );

        $this->assertContains($client->status, [200, 302], 'the password-reminder form was not served');
        $mail = $this->assertMailDelivered(Client::ADMIN_EMAIL);
        $this->assertMailHasLinkContaining($mail, 'param=');
    }

    public function testApiPasswordResetDeliversUsableLink(): void
    {
        $client = new Client();
        $client->postJson('?r=admin/remotecontrol', [
            'method' => 'get_session_key',
            'params' => [Client::ADMIN_USER, Client::ADMIN_PASS],
            'id' => 1,
        ]);
        $decoded = json_decode($client->body, true);
        $this->assertIsString($decoded['result'] ?? null, 'no API session key: ' . substr($client->body, 0, 200));
        $key = $decoded['result'];

        $client->postJson('?r=admin/remotecontrol', [
            'method' => 'reset_user_password',
            'params' => [$key, Client::ADMIN_USER],
            'id' => 2,
        ]);
        $this->assertSame(200, $client->status, 'the API reset call crashed');
        $decoded = json_decode($client->body, true);
        $this->assertSame('OK', $decoded['result']['status'] ?? null, 'the API reset did not succeed: ' . substr($client->body, 0, 200));

        $mail = $this->assertMailDelivered(Client::ADMIN_EMAIL);
        $this->assertMailHasLinkContaining($mail, 'param=');
    }

    public function testAdministratorLoginAndUserManagementStayReachable(): void
    {
        $client = new Client();
        $client->login();
        $this->assertSame(302, $client->status, 'administrator login failed');
        $this->assertStringContainsString('admin', $client->location());

        $client->get('?r=userManagement/index');
        $this->assertSame(200, $client->status, 'the user management page was refused');
        $this->assertGreaterThan(1000, strlen($client->body), 'the user management page was empty');
    }

    public function testNewUserReceivesSetPasswordLink(): void
    {
        $suffix = bin2hex(random_bytes(5));
        $username = 'func_reg_' . $suffix;
        $email = 'func_reg_' . $suffix . '@example.test';
        try {
            $client = new Client();
            $client->login();
            $this->assertSame(302, $client->status, 'administrator login failed');

            $client->submitForm(
                '?r=userManagement/applyEdit',
                '?r=userManagement/index',
                [
                    'User' => [
                        'users_name' => $username,
                        'email' => $email,
                        'full_name' => 'Functional Registration',
                    ],
                    'preset_password' => '0',
                    'password_repeat' => '',
                ]
            );

            $this->assertSame(200, $client->status, 'the new-user action was refused');
            $this->assertStringContainsString('"success":true', $client->body);
            $mail = $this->assertMailDelivered($email);
            $this->assertMailHasLinkContaining($mail, 'param=');

            $stmt = Fixtures::db()->prepare('SELECT COUNT(*) FROM lime_users WHERE users_name = ?');
            $stmt->execute([$username]);
            $this->assertSame(1, (int) $stmt->fetchColumn(), 'the new account was not created');
        } finally {
            Fixtures::deleteUserByName($username);
        }
    }

    public function testBulkResetDeliversLink(): void
    {
        Fixtures::db()->exec('UPDATE lime_users SET last_forgot_email_password = NULL');
        $client = new Client();
        $client->login();
        $this->assertSame(302, $client->status, 'administrator login failed');

        $client->submitForm(
            '?r=userManagement/batchSendAndResetLoginData',
            '?r=userManagement/index',
            ['sItems' => json_encode([Client::BATCH_UID])]
        );

        $this->assertSame(200, $client->status, 'the bulk-reset action was refused');
        $mail = $this->assertMailDelivered(Client::BATCH_EMAIL);
        $this->assertMailHasLinkContaining($mail, 'param=');
    }
}
