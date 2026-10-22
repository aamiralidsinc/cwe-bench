<?php

namespace LsBench;

use PHPUnit\Framework\TestCase;

abstract class BenchCase extends TestCase
{
    protected function setUp(): void
    {
        Fixtures::resetMail();
        Fixtures::clearAllowedHosts();
    }

    protected function tearDown(): void
    {
        Fixtures::clearAllowedHosts();
    }

    /**
     * The attack must end in one of two acceptable states:
     *  - the request is refused with a client error and no email leaves the
     *    application; or
     *  - the email is delivered, and none of its links uses the attacker host,
     *    with at least one link on the configured public host.
     */
    protected function assertAttackBlocked(Client $client, string $attackerHost, ?string $recipient = null): void
    {
        $this->assertSame('', $client->transportError, 'the request did not reach the application');

        $attacker = Fixtures::normalizeHost($attackerHost);
        $mails = $recipient === null ? Fixtures::mails() : Fixtures::mailsTo($recipient);

        foreach ($mails as $mail) {
            foreach (Fixtures::linkHosts($mail) as $host) {
                $this->assertNotSame(
                    $attacker,
                    $host,
                    'an email link used the host supplied by the request: ' . implode(' | ', Fixtures::urls($mail))
                );
            }
        }

        if ($mails === []) {
            $this->assertGreaterThanOrEqual(400, $client->status, 'neither a client error nor an email was produced');
            $this->assertLessThan(500, $client->status, 'the request crashed instead of being served or refused cleanly');
            return;
        }

        $trusted = [];
        foreach ($mails as $mail) {
            foreach (Fixtures::linkHosts($mail) as $host) {
                if ($host === Client::PUBLIC_HOST) {
                    $trusted[] = $mail;
                    break;
                }
            }
        }
        $this->assertNotEmpty($trusted, 'a delivered email has no link on the configured public host');
    }

    /**
     * A protocol-level refusal has no HTTP status of its own: an API can report
     * the refusal in its response body while answering 200. Accept either that
     * (no message at all, and no crash) or a delivered message whose links are
     * all on trusted hosts.
     */
    protected function assertNoMessageOrTrustedLinks(Client $client, string $attackerHost, ?string $recipient = null): void
    {
        $this->assertSame('', $client->transportError, 'the request did not reach the application');

        $attacker = Fixtures::normalizeHost($attackerHost);
        $mails = $recipient === null ? Fixtures::mails() : Fixtures::mailsTo($recipient);

        foreach ($mails as $mail) {
            foreach (Fixtures::linkHosts($mail) as $host) {
                $this->assertNotSame(
                    $attacker,
                    $host,
                    'an email link used the host supplied by the request: ' . implode(' | ', Fixtures::urls($mail))
                );
            }
        }

        if ($mails === []) {
            $this->assertLessThan(500, $client->status, 'the request crashed instead of being served or refused cleanly');
            return;
        }

        $trusted = [];
        foreach ($mails as $mail) {
            foreach (Fixtures::linkHosts($mail) as $host) {
                if ($host === Client::PUBLIC_HOST) {
                    $trusted[] = $mail;
                    break;
                }
            }
        }
        $this->assertNotEmpty($trusted, 'a delivered email has no link on the configured public host');
    }

    protected function assertMailDelivered(string $recipient): array
    {
        $mails = Fixtures::mailsTo($recipient);
        $this->assertNotEmpty($mails, 'no email was delivered to ' . $recipient);
        return $mails[0];
    }

    protected function assertMailHasLinkContaining(array $mail, string $needle): void
    {
        foreach (Fixtures::urls($mail) as $url) {
            if (str_contains($url, $needle)) {
                $this->assertTrue(true);
                return;
            }
        }
        $this->fail(
            'no link containing "' . $needle . '" in the delivered email; links: '
            . implode(' | ', Fixtures::urls($mail))
        );
    }
}
