<?php

namespace LsBench\Tests\Security;

use LsBench\BenchCase;
use LsBench\Client;
use LsBench\Fixtures;

/**
 * A participant-facing confirmation email built by the survey registration
 * flow. The message also contains the standard survey link; the whole message
 * must be free of request-supplied hosts.
 */
class SurveyRegistrationHostTest extends BenchCase
{
    private string $email = '';

    protected function setUp(): void
    {
        parent::setUp();
        $this->email = 'sec_survey_' . bin2hex(random_bytes(5)) . '@example.test';
    }

    protected function tearDown(): void
    {
        Fixtures::deleteTokenByEmail($this->email);
        parent::tearDown();
    }

    public function testRegistrationEmailLinksDoNotFollowAttackerHost(): void
    {
        $client = new Client();
        $client->submitForm(
            '?r=register/index&sid=' . Client::SURVEY_ID,
            '?r=register/index&sid=' . Client::SURVEY_ID,
            [
                'register' => '1',
                'sid' => (string) Client::SURVEY_ID,
                'register_firstname' => 'Security',
                'register_lastname' => 'Participant',
                'register_email' => $this->email,
            ],
            'attacker.example'
        );

        $this->assertAttackBlocked($client, 'attacker.example', $this->email);
    }
}
