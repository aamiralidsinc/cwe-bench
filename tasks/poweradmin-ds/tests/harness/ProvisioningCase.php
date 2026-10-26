<?php

/**
 * Shared fixtures for the hidden suites: a throw-away database built from the product's own
 * schema files, production user-info value objects, and the provisioning service wired to a
 * configuration the test controls. Everything here is bookkeeping owned by the verifier.
 */

declare(strict_types=1);

namespace Poweradmin\HiddenTests;

use PDO;
use PHPUnit\Framework\TestCase;
use Poweradmin\Application\Service\UserProvisioningService;
use Poweradmin\Domain\ValueObject\OidcUserInfo;
use Poweradmin\Domain\ValueObject\SamlUserInfo;
use Poweradmin\Infrastructure\Configuration\ConfigurationManager;
use Poweradmin\Infrastructure\Logger\Logger;
use Poweradmin\Infrastructure\Logger\NullLogHandler;

abstract class ProvisioningCase extends TestCase
{
    protected string $workspace;
    protected string $provider = 'corp-idp';

    /** @var string[] Databases created by the current test, dropped in tearDown. */
    private array $databases = [];

    protected function setUp(): void
    {
        parent::setUp();
        $workspace = getenv('PA_WORKSPACE');
        $this->workspace = is_string($workspace) && $workspace !== '' ? $workspace : '/workspace';
    }

    protected function tearDown(): void
    {
        foreach ($this->databases as $name) {
            try {
                $this->adminConnection()->exec("DROP DATABASE IF EXISTS `{$name}`");
            } catch (\Throwable) {
                // A database that cannot be dropped must not turn a passing test into an error.
            }
        }
        $this->databases = [];
        parent::tearDown();
    }

    // ---- connections -----------------------------------------------------------------

    private function dbHost(): string
    {
        return getenv('PA_DB_HOST') ?: '127.0.0.1';
    }

    private function dbPort(): string
    {
        return getenv('PA_DB_PORT') ?: '3307';
    }

    private function dbUser(): string
    {
        return getenv('PA_DB_USER') ?: 'pa';
    }

    private function dbPass(): string
    {
        return getenv('PA_DB_PASS') ?: '';
    }

    private function adminConnection(): PDO
    {
        return new PDO(
            sprintf('mysql:host=%s;port=%s;charset=utf8mb4', $this->dbHost(), $this->dbPort()),
            $this->dbUser(),
            $this->dbPass(),
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );
    }

    private function mysqlDsn(string $database): string
    {
        return sprintf(
            'mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
            $this->dbHost(),
            $this->dbPort(),
            $database
        );
    }

    /**
     * A fresh MySQL database created from the product's shipped schema file. When
     * $latin1IdentityTables is set, the two identity-link tables are converted to the
     * latin1 character set, as an installation created with that character set would be.
     */
    protected function mysqlDatabase(bool $latin1IdentityTables = false): PDO
    {
        $admin = $this->adminConnection();
        $name = 'pa_t_' . bin2hex(random_bytes(6));
        $admin->exec("CREATE DATABASE `{$name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
        $this->databases[] = $name;

        $pdo = new PDO(
            $this->mysqlDsn($name),
            $this->dbUser(),
            $this->dbPass(),
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::MYSQL_ATTR_MULTI_STATEMENTS => true]
        );

        $schema = $this->workspace . '/sql/poweradmin-mysql-db-structure.sql';
        $pdo->exec((string) file_get_contents($schema));

        if ($latin1IdentityTables) {
            $pdo->exec('SET FOREIGN_KEY_CHECKS = 0');
            $pdo->exec('ALTER TABLE oidc_user_links CONVERT TO CHARACTER SET latin1 COLLATE latin1_swedish_ci');
            $pdo->exec('ALTER TABLE saml_user_links CONVERT TO CHARACTER SET latin1 COLLATE latin1_swedish_ci');
            $pdo->exec('SET FOREIGN_KEY_CHECKS = 1');
        }

        return $pdo;
    }

    /** A fresh in-memory SQLite database created from the product's shipped schema file. */
    protected function sqliteDatabase(): PDO
    {
        $pdo = new PDO('sqlite::memory:');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $schema = $this->workspace . '/sql/poweradmin-sqlite-db-structure.sql';
        $pdo->exec((string) file_get_contents($schema));
        return $pdo;
    }

    // ---- service ---------------------------------------------------------------------

    protected function configuration(bool $linkByEmail = false, bool $autoProvision = true): ConfigurationManager
    {
        $settings = [
            'enabled' => true,
            'link_by_email' => $linkByEmail,
            'auto_provision' => $autoProvision,
            'sync_user_info' => true,
            'default_permission_template' => 'Administrator',
            'permission_template_mapping' => [],
            'group_mapping' => [],
        ];

        $config = $this->createMock(ConfigurationManager::class);
        $config->method('getGroup')->willReturnCallback(
            static fn (string $group): array => in_array($group, ['oidc', 'saml'], true) ? $settings : []
        );
        $config->method('get')->willReturnCallback(
            static function (string $group, string $key, mixed $default = null) use ($settings): mixed {
                if (in_array($group, ['oidc', 'saml'], true)) {
                    return array_key_exists($key, $settings) ? $settings[$key] : $default;
                }
                return $default;
            }
        );

        return $config;
    }

    protected function service(PDO $db, ?ConfigurationManager $config = null): UserProvisioningService
    {
        return new UserProvisioningService(
            $db,
            $config ?? $this->configuration(),
            new Logger(new NullLogHandler(), 'error')
        );
    }

    // ---- fixtures --------------------------------------------------------------------

    protected function seedUser(
        PDO $db,
        string $username,
        string $email,
        string $authMethod = 'oidc'
    ): int {
        $stmt = $db->prepare(
            'INSERT INTO users (username, password, fullname, email, description, perm_templ, '
            . 'active, use_ldap, auth_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        );
        $stmt->execute([$username, '', $username, $email, '', 1, 1, 0, $authMethod]);
        return (int) $db->lastInsertId();
    }

    protected function seedOidcLink(
        PDO $db,
        int $userId,
        string $provider,
        string $subject,
        string $username,
        string $email
    ): void {
        $stmt = $db->prepare(
            'INSERT INTO oidc_user_links (user_id, provider_id, oidc_subject, username, email) '
            . 'VALUES (?, ?, ?, ?, ?)'
        );
        $stmt->execute([$userId, $provider, $subject, $username, $email]);
    }

    protected function seedSamlLink(
        PDO $db,
        int $userId,
        string $provider,
        string $subject,
        string $username,
        string $email
    ): void {
        $stmt = $db->prepare(
            'INSERT INTO saml_user_links (user_id, provider_id, saml_subject, username, email) '
            . 'VALUES (?, ?, ?, ?, ?)'
        );
        $stmt->execute([$userId, $provider, $subject, $username, $email]);
    }

    protected function oidcIdentity(
        string $subject,
        string $provider = 'corp-idp',
        string $username = 'signer-in',
        string $email = 'signer-in@example.test'
    ): OidcUserInfo {
        return new OidcUserInfo(
            username: $username,
            email: $email,
            displayName: 'Signer In',
            providerId: $provider,
            subject: $subject
        );
    }

    protected function samlIdentity(
        string $subject,
        string $provider = 'corp-idp',
        string $username = 'signer-in',
        string $email = 'signer-in@example.test'
    ): SamlUserInfo {
        return new SamlUserInfo(
            username: $username,
            email: $email,
            displayName: 'Signer In',
            providerId: $provider,
            nameId: $subject
        );
    }

    // ---- observations ----------------------------------------------------------------

    protected function userRow(PDO $db, int $userId): array
    {
        $stmt = $db->prepare('SELECT id, username, fullname, email, auth_method FROM users WHERE id = ?');
        $stmt->execute([$userId]);
        return $stmt->fetch(PDO::FETCH_ASSOC) ?: [];
    }

    protected function oidcLinks(PDO $db): array
    {
        return $db->query(
            'SELECT id, user_id, provider_id, oidc_subject FROM oidc_user_links ORDER BY id'
        )->fetchAll(PDO::FETCH_ASSOC);
    }

    protected function samlLinks(PDO $db): array
    {
        return $db->query(
            'SELECT id, user_id, provider_id, saml_subject FROM saml_user_links ORDER BY id'
        )->fetchAll(PDO::FETCH_ASSOC);
    }

    /**
     * The local account and link that belong to $userId must still describe the same
     * identity after a different identity was presented.
     */
    protected function assertAccountStillBound(PDO $db, int $userId, string $table, string $subjectColumn, string $provider, string $subject): void
    {
        $this->assertSame($userId, (int) $this->userRow($db, $userId)['id'], 'the account was removed');

        $stmt = $db->prepare(
            "SELECT user_id FROM {$table} WHERE {$subjectColumn} = ? AND provider_id = ? ORDER BY id"
        );
        $stmt->execute([$subject, $provider]);
        $owners = array_map(static fn (array $row): int => (int) $row['user_id'], $stmt->fetchAll(PDO::FETCH_ASSOC));

        $this->assertContains(
            $userId,
            $owners,
            "the binding for the existing identity ({$subject}) is no longer held by its account"
        );
    }
}
