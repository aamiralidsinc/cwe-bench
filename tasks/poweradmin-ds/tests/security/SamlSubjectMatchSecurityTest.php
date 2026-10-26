<?php

/**
 * The same identity rule applies to the SAML sign-in path: the asserted name identifier
 * must be matched as the exact character sequence that is stored.
 */

declare(strict_types=1);

namespace Poweradmin\HiddenTests\Security;

use PDO;
use Poweradmin\HiddenTests\ProvisioningCase;

final class SamlSubjectMatchSecurityTest extends ProvisioningCase
{
    private PDO $db;
    private int $victim;

    protected function setUp(): void
    {
        parent::setUp();
        $this->db = $this->mysqlDatabase();
        $this->victim = $this->seedUser($this->db, 'victim', 'victim@example.test', 'saml');
        $this->seedSamlLink(
            $this->db,
            $this->victim,
            $this->provider,
            'VictimSubject',
            'victim',
            'victim@example.test'
        );
    }

    private function provisionAs(string $subject): ?int
    {
        return $this->service($this->db)->provisionUser(
            $this->samlIdentity($subject, $this->provider),
            $this->provider
        );
    }

    public function testCaseVariantNameIdDoesNotReachAnotherAccount(): void
    {
        $resolved = $this->provisionAs('victimsubject');
        $this->assertNotSame($this->victim, $resolved, 'a different name identifier was signed in to the existing account');
        $this->assertSame(
            'victim@example.test',
            $this->userRow($this->db, $this->victim)['email'],
            'the existing account was updated'
        );
        $this->assertAccountStillBound(
            $this->db,
            $this->victim,
            'saml_user_links',
            'saml_subject',
            $this->provider,
            'VictimSubject'
        );
    }

    public function testTrailingSpaceVariantNameIdDoesNotReachAnotherAccount(): void
    {
        $resolved = $this->provisionAs('VictimSubject ');
        $this->assertNotSame($this->victim, $resolved, 'a different name identifier was signed in to the existing account');
        $this->assertAccountStillBound(
            $this->db,
            $this->victim,
            'saml_user_links',
            'saml_subject',
            $this->provider,
            'VictimSubject'
        );
    }
}
