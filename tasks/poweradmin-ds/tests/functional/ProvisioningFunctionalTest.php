<?php

/**
 * Ordinary sign-in behaviour that must keep working: exact identities resolve to their own
 * account, new identities are provisioned once, configured email linking still binds an
 * identity to an existing account, and different providers stay separate.
 */

declare(strict_types=1);

namespace Poweradmin\HiddenTests\Functional;

use PDO;
use Poweradmin\HiddenTests\ProvisioningCase;

final class ProvisioningFunctionalTest extends ProvisioningCase
{
    private PDO $db;

    protected function setUp(): void
    {
        parent::setUp();
        $this->db = $this->mysqlDatabase();
    }

    public function testOidcExactSubjectSignsIntoItsAccount(): void
    {
        $victim = $this->seedUser($this->db, 'victim', 'victim@example.test', 'oidc');
        $this->seedOidcLink($this->db, $victim, $this->provider, 'VictimSubject', 'victim', 'victim@example.test');

        $service = $this->service($this->db);
        $first = $service->provisionUser(
            $this->oidcIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );
        $second = $service->provisionUser(
            $this->oidcIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );

        $this->assertSame($victim, $first);
        $this->assertSame($victim, $second);
        $this->assertCount(1, $this->oidcLinks($this->db));
        $this->assertSame('victim@example.test', $this->userRow($this->db, $victim)['email']);
    }

    public function testSamlExactSubjectSignsIntoItsAccount(): void
    {
        $victim = $this->seedUser($this->db, 'victim', 'victim@example.test', 'saml');
        $this->seedSamlLink($this->db, $victim, $this->provider, 'VictimSubject', 'victim', 'victim@example.test');

        $service = $this->service($this->db);
        $resolved = $service->provisionUser(
            $this->samlIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );

        $this->assertSame($victim, $resolved);
        $this->assertCount(1, $this->samlLinks($this->db));
    }

    public function testNewIdentityIsProvisionedOnceAndStaysBound(): void
    {
        $service = $this->service($this->db);
        $first = $service->provisionUser(
            $this->oidcIdentity('BrandNewSubject', $this->provider, 'newcomer', 'newcomer@example.test'),
            $this->provider
        );
        $this->assertNotNull($first);

        $second = $service->provisionUser(
            $this->oidcIdentity('BrandNewSubject', $this->provider, 'newcomer', 'newcomer@example.test'),
            $this->provider
        );
        $this->assertSame($first, $second, 'the same new identity resolved to two accounts');
        $this->assertSame('newcomer', $this->userRow($this->db, $first)['username']);
        $this->assertCount(1, $this->oidcLinks($this->db));
    }

    public function testEmailLinkingBindsIdentityToExistingAccount(): void
    {
        $existing = $this->seedUser($this->db, 'existing', 'existing@example.test', 'sql');

        $service = $this->service($this->db, $this->configuration(true));
        $resolved = $service->provisionUser(
            $this->oidcIdentity('SomeOtherSubject', $this->provider, 'existing', 'existing@example.test'),
            $this->provider
        );

        $this->assertSame($existing, $resolved, 'configured email linking stopped binding to the existing account');
        $links = $this->oidcLinks($this->db);
        $this->assertCount(1, $links);
        $this->assertSame($existing, (int) $links[0]['user_id']);
    }

    public function testLegitimateNonAsciiSubjectSignsIn(): void
    {
        $victim = $this->seedUser($this->db, 'jose', 'jose@example.test', 'oidc');
        $this->seedOidcLink($this->db, $victim, $this->provider, "Jos\u{e9}", 'jose', 'jose@example.test');

        $resolved = $this->service($this->db)->provisionUser(
            $this->oidcIdentity("Jos\u{e9}", $this->provider, 'jose', 'jose@example.test'),
            $this->provider
        );

        $this->assertSame($victim, $resolved);
    }

    public function testDifferentProvidersKeepSeparateAccounts(): void
    {
        $victim = $this->seedUser($this->db, 'victim', 'victim@example.test', 'oidc');
        $this->seedOidcLink($this->db, $victim, $this->provider, 'SharedSubject', 'victim', 'victim@example.test');

        $service = $this->service($this->db);
        $first = $service->provisionUser(
            $this->oidcIdentity('SharedSubject', 'other-idp', 'other', 'other@example.test'),
            'other-idp'
        );
        $second = $service->provisionUser(
            $this->oidcIdentity('SharedSubject', 'other-idp', 'other', 'other@example.test'),
            'other-idp'
        );

        $this->assertNotSame($victim, $first, 'a subject from another provider resolved to the existing account');
        $this->assertSame($first, $second, 'the same identity from the other provider resolved to two accounts');
    }
}
