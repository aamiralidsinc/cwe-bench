<?php

namespace LsBench\Tests\Functional;

use LsBench\BenchCase;
use LsBench\Client;
use LsBench\Fixtures;

/**
 * Participant mail keeps working: registration confirmations still reach the
 * participant with a usable survey link, and the withdrawal-link message still
 * carries the participant's token.
 */
class ParticipantEmailFunctionalTest extends BenchCase
{
    public function testSurveyRegistrationEmailKeepsItsLinks(): void
    {
        $email = 'func_survey_' . bin2hex(random_bytes(5)) . '@example.test';
        try {
            $client = new Client();
            $client->submitForm(
                '?r=register/index&sid=' . Client::SURVEY_ID,
                '?r=register/index&sid=' . Client::SURVEY_ID,
                [
                    'register' => '1',
                    'sid' => (string) Client::SURVEY_ID,
                    'register_firstname' => 'Functional',
                    'register_lastname' => 'Participant',
                    'register_email' => $email,
                ]
            );

            $this->assertSame(200, $client->status, 'the registration form was refused');
            $mail = $this->assertMailDelivered($email);
            $this->assertMailHasLinkContaining($mail, 'token=');
            $this->assertMailHasLinkContaining($mail, 'sid=' . Client::SURVEY_ID);
            $this->assertStringContainsString('Direct link:', $mail['body']);
        } finally {
            Fixtures::deleteTokenByEmail($email);
        }
    }

    public function testSurveyLinkReminderKeepsItsLink(): void
    {
        $client = new Client();
        $client->get(
            '?r=survey/emaillink&sid=' . Client::SURVEY_ID
            . '&token=' . Client::PARTICIPANT_TOKEN
        );

        $this->assertSame(200, $client->status, 'the survey-link reminder was refused');
        $mail = $this->assertMailDelivered('participant@example.org');
        $this->assertMailHasLinkContaining($mail, 'token=' . Client::PARTICIPANT_TOKEN);
        $this->assertMailHasLinkContaining($mail, 'sid=' . Client::SURVEY_ID);
    }

    public function testWithdrawalConfirmationEmailKeepsItsLink(): void
    {
        $client = new Client();
        $client->get(
            '?r=optout/emailtokens&surveyid=' . Client::SURVEY_ID
            . '&token=' . Client::PARTICIPANT_TOKEN
        );

        $this->assertSame(200, $client->status, 'the withdrawal-link page was refused');
        $mail = $this->assertMailDelivered('participant@example.org');
        $this->assertMailHasLinkContaining($mail, Client::PARTICIPANT_TOKEN);
        $this->assertMailHasLinkContaining($mail, 'surveyid=' . Client::SURVEY_ID);
    }
}
