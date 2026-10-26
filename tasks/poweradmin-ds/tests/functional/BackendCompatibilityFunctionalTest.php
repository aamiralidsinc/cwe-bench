<?php

/**
 * The product supports more than one database backend and installations are created with
 * different database character sets; ordinary sign-in must keep working on each of them.
 */

declare(strict_types=1);

namespace Poweradmin\HiddenTests\Functional;

use PDO;
use Poweradmin\HiddenTests\ProvisioningCase;

final class BackendCompatibilityFunctionalTest extends ProvisioningCase
{
    public function testSqliteExactSubjectSignsIntoItsAccount(): void
    {
        $db = $this->sqliteDatabase();
        $victim = $this->seedUser($db, 'victim', 'victim@example.test', 'oidc');
        $this->seedOidcLink($db, $victim, $this->provider, 'VictimSubject', 'victim', 'victim@example.test');

        $service = $this->service($db);
        $first = $service->provisionUser(
            $this->oidcIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );
        $second = $service->provisionUser(
            $this->oidcIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );

        $this->assertSame($victim, $first, 'an existing identity no longer signs in on the SQLite backend');
        $this->assertSame($victim, $second);
    }

    public function testSqliteDistinctIdentitiesStaySeparate(): void
    {
        $db = $this->sqliteDatabase();
        $victim = $this->seedUser($db, 'victim', 'victim@example.test', 'oidc');
        $this->seedOidcLink($db, $victim, $this->provider, 'VictimSubject', 'victim', 'victim@example.test');

        $service = $this->service($db);
        $first = $service->provisionUser(
            $this->oidcIdentity('victimsubject', $this->provider, 'other', 'other@example.test'),
            $this->provider
        );
        $second = $service->provisionUser(
            $this->oidcIdentity('victimsubject', $this->provider, 'other', 'other@example.test'),
            $this->provider
        );

        $this->assertNotSame($victim, $first, 'a distinct identity resolved to the existing account on SQLite');
        $this->assertSame($first, $second, 'a distinct identity was provisioned twice on SQLite');
    }

    public function testLatin1InstallResolvesExistingSubject(): void
    {
        $db = $this->mysqlDatabase(true);
        $victim = $this->seedUser($db, 'victim', 'victim@example.test', 'oidc');
        $this->seedOidcLink($db, $victim, $this->provider, 'VictimSubject', 'victim', 'victim@example.test');

        $service = $this->service($db);
        $first = $service->provisionUser(
            $this->oidcIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );
        $second = $service->provisionUser(
            $this->oidcIdentity('VictimSubject', $this->provider, 'victim', 'victim@example.test'),
            $this->provider
        );

        $this->assertSame($victim, $first, 'an existing identity no longer signs in on a latin1 installation');
        $this->assertSame($victim, $second, 'an existing identity was re-provisioned on a latin1 installation');
        $this->assertCount(1, $this->oidcLinks($db));
    }
}
