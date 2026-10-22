<?php

namespace LsBench\Tests\Security;

use LsBench\BenchCase;
use LsBench\Client;

/**
 * A participant-facing message on the public withdrawal path. It carries the
 * participant's access token, so its link host must not follow the request.
 */
class OptoutConfirmationHostTest extends BenchCase
{
    public function testWithdrawalEmailLinkDoesNotFollowAttackerHost(): void
    {
        $client = new Client();
        $client->get(
            '?r=optout/emailtokens&surveyid=' . Client::SURVEY_ID
            . '&token=' . Client::PARTICIPANT_TOKEN,
            'attacker.example'
        );

        $this->assertAttackBlocked($client, 'attacker.example', 'participant@example.org');
    }
}
