<?php

/**
 * An external subject identifies exactly one local account. A subject that is a different
 * character sequence from a stored one must never resolve to that stored identity's account.
 */

declare(strict_types=1);

namespace Poweradmin\HiddenTests\Security;

use PDO;
use Poweradmin\HiddenTests\ProvisioningCase;

final class OidcSubjectMatchSecurityTest extends ProvisioningCase
{
    private PDO $db;
    private int $victim;

    protected function setUp(): void
    {
        parent::setUp();
        $this->db = $this->mysqlDatabase();
        $this->victim = $this->seedUser($this->db, 'victim', 'victim@example.test', 'oidc');
        $this->seedOidcLink(
            $this->db,
            $this->victim,
            $this->provider,
            'VictimSubject',
            'victim',
            'victim@example.test'
        );
    }

    private function provisionAs(string $subject, ?string $providerOverride = null): ?int
    {
        $provider = $providerOverride ?? $this->provider;
        return $this->service($this->db)->provisionUser(
            $this->oidcIdentity($subject, $provider),
            $provider
        );
    }

    private function assertDidNotReachVictim(?int $resolved): void
    {
        $this->assertNotSame($this->victim, $resolved, 'a different subject was signed in to the existing account');
        $row = $this->userRow($this->db, $this->victim);
        $this->assertSame('victim@example.test', $row['email'], 'the existing account was updated');
    }

    public function testCaseVariantSubjectDoesNotReachAnotherAccount(): void
    {
        $this->assertDidNotReachVictim($this->provisionAs('victimsubject'));
        $this->assertAccountStillBound(
            $this->db,
            $this->victim,
            'oidc_user_links',
            'oidc_subject',
            $this->provider,
            'VictimSubject'
        );
    }

    public function testAccentVariantSubjectDoesNotReachAnotherAccount(): void
    {
        $this->db->exec("UPDATE oidc_user_links SET oidc_subject = 'Jos\u{e9}'");
        $this->assertDidNotReachVictim($this->provisionAs('Jose'));
    }

    public function testTrailingSpaceVariantSubjectDoesNotReachAnotherAccount(): void
    {
        $this->assertDidNotReachVictim($this->provisionAs('VictimSubject '));
        $this->assertAccountStillBound(
            $this->db,
            $this->victim,
            'oidc_user_links',
            'oidc_subject',
            $this->provider,
            'VictimSubject'
        );
    }

    public function testProviderIdCaseVariantDoesNotReachAnotherAccount(): void
    {
        $this->assertDidNotReachVictim($this->provisionAs('VictimSubject', 'CORP-IDP'));
        $this->assertAccountStillBound(
            $this->db,
            $this->victim,
            'oidc_user_links',
            'oidc_subject',
            $this->provider,
            'VictimSubject'
        );
    }

    /**
     * Two distinct subjects must keep two distinct, stable account bindings: the second
     * sign-in of the new subject must find the account created for it, and the existing
     * account must stay bound to its own subject.
     */
    public function testDistinctIdentityKeepsItsOwnStableAccount(): void
    {
        $first = $this->provisionAs('victimsubject');
        $this->assertNotSame($this->victim, $first, 'a different subject was signed in to the existing account');
        $this->assertNotNull($first, 'the distinct identity could not sign in at all');

        $second = $this->provisionAs('victimsubject');
        $this->assertSame($first, $second, 'the same subject resolved to a different account on the next sign-in');

        $links = $this->oidcLinks($this->db);
        $this->assertCount(2, $links, 'the two identities do not both have a binding');
        $owners = array_map(static fn (array $row): int => (int) $row['user_id'], $links);
        $this->assertContains($this->victim, $owners);
        $this->assertContains($first, $owners);
        $this->assertNotSame(
            $owners[0],
            $owners[1],
            'the two identities share one account'
        );
    }
}
