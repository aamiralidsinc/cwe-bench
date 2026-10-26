<?php

/**
 * When a sign-in has to store a new binding, the exactness rule still applies: storing an
 * identity must not move, overwrite or take over the binding or account of a different
 * identity that is already stored.
 */

declare(strict_types=1);

namespace Poweradmin\HiddenTests\Security;

use PDO;
use Poweradmin\HiddenTests\ProvisioningCase;

final class IdentityBindingSecurityTest extends ProvisioningCase
{
    private PDO $db;
    private int $victim;

    protected function setUp(): void
    {
        parent::setUp();
        $this->db = $this->mysqlDatabase();
        $this->victim = $this->seedUser($this->db, 'victim', 'victim@example.test', 'oidc');
    }

    public function testOidcSignInDoesNotTakeOverAnotherStoredBinding(): void
    {
        $this->seedOidcLink(
            $this->db,
            $this->victim,
            $this->provider,
            'VictimSubject',
            'victim',
            'victim@example.test'
        );

        $service = $this->service($this->db);
        $resolved = $service->provisionUser(
            $this->oidcIdentity('victimsubject', $this->provider),
            $this->provider
        );

        $this->assertNotSame($this->victim, $resolved, 'a different subject was signed in to the existing account');
        $this->assertAccountStillBound(
            $this->db,
            $this->victim,
            'oidc_user_links',
            'oidc_subject',
            $this->provider,
            'VictimSubject'
        );

        $victimSignIn = $service->provisionUser(
            $this->oidcIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );
        $this->assertSame($this->victim, $victimSignIn, 'the existing subject no longer signs in to its own account');
    }

    public function testSamlSignInDoesNotTakeOverAnotherStoredBinding(): void
    {
        $this->seedSamlLink(
            $this->db,
            $this->victim,
            $this->provider,
            'VictimSubject',
            'victim',
            'victim@example.test'
        );

        $service = $this->service($this->db);
        $resolved = $service->provisionUser(
            $this->samlIdentity('victimsubject', $this->provider),
            $this->provider
        );

        $this->assertNotSame($this->victim, $resolved, 'a different name identifier was signed in to the existing account');
        $this->assertAccountStillBound(
            $this->db,
            $this->victim,
            'saml_user_links',
            'saml_subject',
            $this->provider,
            'VictimSubject'
        );

        $victimSignIn = $service->provisionUser(
            $this->samlIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );
        $this->assertSame($this->victim, $victimSignIn, 'the existing subject no longer signs in to its own account');
    }
}
