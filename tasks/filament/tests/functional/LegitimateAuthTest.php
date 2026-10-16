<?php

namespace CweTests\Functional;

use CweTests\TestCase;
use Filament\Actions\Testing\TestAction;
use Filament\Auth\Pages\Login;
use Filament\Facades\Filament;
use Filament\Tests\Fixtures\Models\User;
use Illuminate\Support\Arr;

use function Filament\Tests\livewire;

/**
 * Legitimate sign-in through the login page and its multi-factor challenge must
 * keep working: a valid password still produces a challenge, a valid one-time code
 * and a valid recovery code each complete authentication, and a wrong password is
 * still rejected.
 */
class LegitimateAuthTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Filament::setCurrentPanel('app-authentication');
    }

    public function test_valid_login_presents_the_challenge(): void
    {
        $user = User::factory()->hasAppAuthentication()->create();

        livewire(Login::class)
            ->fillForm(['email' => $user->email, 'password' => 'password'])
            ->call('authenticate')
            ->assertNotSet('userUndertakingMultiFactorAuthentication', null)
            ->assertNoRedirect();

        $this->assertGuest();
    }

    public function test_valid_one_time_code_completes_authentication(): void
    {
        $provider = Arr::first(Filament::getCurrentOrDefaultPanel()->getMultiFactorAuthenticationProviders());
        $user = User::factory()->hasAppAuthentication()->create();

        livewire(Login::class)
            ->fillForm(['email' => $user->email, 'password' => 'password'])
            ->call('authenticate')
            ->fillForm([$provider->getId() => ['code' => $provider->getCurrentCode($user)]], 'multiFactorChallengeForm')
            ->call('authenticate')
            ->assertHasNoErrors()
            ->assertRedirect(Filament::getUrl());

        $this->assertAuthenticatedAs($user);
    }

    public function test_valid_recovery_code_completes_authentication(): void
    {
        $provider = Arr::first(Filament::getCurrentOrDefaultPanel()->getMultiFactorAuthenticationProviders());
        $recoveryCodes = $provider->generateRecoveryCodes();
        $user = User::factory()->hasAppAuthentication($recoveryCodes)->create();

        livewire(Login::class)
            ->fillForm(['email' => $user->email, 'password' => 'password'])
            ->call('authenticate')
            ->callAction(TestAction::make('useRecoveryCode')
                ->schemaComponent("{$provider->getId()}.code", schema: 'multiFactorChallengeForm'))
            ->fillForm([$provider->getId() => ['recoveryCode' => Arr::first($recoveryCodes)]], 'multiFactorChallengeForm')
            ->call('authenticate')
            ->assertHasNoErrors()
            ->assertRedirect(Filament::getUrl());

        $this->assertAuthenticatedAs($user);
    }

    public function test_invalid_password_is_rejected(): void
    {
        $user = User::factory()->hasAppAuthentication()->create();

        livewire(Login::class)
            ->fillForm(['email' => $user->email, 'password' => 'wrong-password'])
            ->call('authenticate')
            ->assertHasFormErrors(['email'])
            ->assertNoRedirect();

        $this->assertGuest();
    }
}
