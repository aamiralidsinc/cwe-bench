<?php

namespace LsBench\Tests\Security;

use LsBench\BenchCase;
use LsBench\Client;

/**
 * A public participant utility that mails the survey link again. Its base URL
 * helper prefers an address supplied in the request's forwarded headers, so the
 * request host itself is not where the attacker-controlled value arrives.
 */
class ForwardedHostMailTest extends BenchCase
{
    public function testSurveyLinkEmailDoesNotFollowForwardedHost(): void
    {
        $client = new Client();
        $client->get(
            '?r=survey/emaillink&sid=' . Client::SURVEY_ID
            . '&token=' . Client::PARTICIPANT_TOKEN,
            Client::LEGIT_HOST,
            ['X-Forwarded-Host: attacker.example', 'X-Forwarded-Proto: http']
        );

        $this->assertAttackBlocked($client, 'attacker.example', 'participant@example.org');
    }
}
