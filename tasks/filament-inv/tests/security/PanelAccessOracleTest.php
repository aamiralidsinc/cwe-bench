<?php

namespace CweTests\Security;

use CweTests\TestCase;
use Filament\Auth\Pages\Login;
use Filament\Facades\Filament;
use Filament\Tests\Fixtures\Models\User;

use function Filament\Tests\livewire;

/**
 * On a panel that the account is forbidden to access, the login page must behave
 * identically whether the submitted password is right or wrong. If a correct
 * password produces a multi-factor challenge while a wrong one produces a generic
 * error, an unauthenticated attacker can confirm password validity.
 */
class PanelAccessOracleTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        // 'inaccessible-mfa' is a panel with multi-factor auth whose id is absent
        // from the User fixture's canAccessPanel() allow-list, so every user is denied.
        Filament::setCurrentPanel('inaccessible-mfa');
    }

    private function outcomeFor(User $user, string $password): array
    {
        $lw = livewire(Login::class)
            ->fillForm(['email' => $user->email, 'password' => $password])
            ->call('authenticate');

        return [
            'challengePresented' => $lw->get('userUndertakingMultiFactorAuthentication') !== null,
            'errors' => array_keys($lw->errors()->toArray()),
        ];
    }

    public function test_correct_password_does_not_present_a_challenge_for_a_denied_account(): void
    {
        $user = User::factory()->hasAppAuthentication()->create();

        livewire(Login::class)
            ->fillForm(['email' => $user->email, 'password' => 'password'])
            ->call('authenticate')
            ->assertSet('userUndertakingMultiFactorAuthentication', null)
            ->assertHasFormErrors(['email']);

        $this->assertGuest();
    }

    public function test_correct_and_incorrect_password_are_indistinguishable_for_a_denied_account(): void
    {
        $user = User::factory()->hasAppAuthentication()->create();

        $this->assertSame(
            $this->outcomeFor($user, 'password'),
            $this->outcomeFor($user, 'definitely-not-the-password'),
        );

        $this->assertGuest();
    }
}
