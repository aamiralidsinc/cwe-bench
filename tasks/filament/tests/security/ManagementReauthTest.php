<?php

namespace CweTests\Security;

use CweTests\AssertsRefusal;
use CweTests\TestCase;
use Filament\Actions\Testing\TestAction;
use Filament\Auth\Pages\EditProfile;
use Filament\Facades\Filament;
use Filament\Tests\Fixtures\Models\User;
use Illuminate\Support\Arr;

use function Filament\Tests\livewire;

/**
 * Disabling app-based multi-factor authentication is a sensitive account change.
 * It must require the account holder to re-enter their current password, so that
 * someone who merely holds a live session (but not the password) cannot strip the
 * second factor off the account.
 *
 * 2026-10-16: the attempt used to be wrapped in catch (\Throwable), so a fix that crashed
 * (TypeError, undefined key, HTTP 500) on a missing password counted as a refusal. An
 * exception that escapes must now be one the application answers with a client error (4xx,
 * e.g. validation or authorization), and a returned response must not be a crash (5xx, or
 * Livewire's 419 for a TypeError). An in-form refusal (validation error, halted action) raises
 * nothing and is judged by the side effect: the second factor stays enabled.
 */
class ManagementReauthTest extends TestCase
{
    use AssertsRefusal;
    protected function setUp(): void
    {
        parent::setUp();
        Filament::setCurrentPanel('app-authentication');
    }

    private function makeUserWithMfa(): User
    {
        $provider = Arr::first(Filament::getCurrentOrDefaultPanel()->getMultiFactorAuthenticationProviders());
        $user = User::factory()->hasAppAuthentication($provider->generateRecoveryCodes())->create();
        $this->actingAs($user);

        return $user;
    }

    public function test_disabling_mfa_without_a_password_is_rejected(): void
    {
        $provider = Arr::first(Filament::getCurrentOrDefaultPanel()->getMultiFactorAuthenticationProviders());
        $user = $this->makeUserWithMfa();

        try {
            $component = livewire(EditProfile::class)
                ->callAction(
                    TestAction::make('disableAppAuthentication')->schemaComponent('app', schema: 'content'),
                    ['code' => $provider->getCurrentCode($user)],
                );

            $this->assertComponentDidNotCrash($component, 'the request to turn off the second factor');
        } catch (\PHPUnit\Framework\AssertionFailedError $e) {
            throw $e;
        } catch (\Throwable $e) {
            $this->assertExceptionIsRefusal($e, 'the request to turn off the second factor');
        }

        // The second factor must still be enabled.
        $this->assertTrue(filled($user->fresh()->getAppAuthenticationSecret()));
        $this->assertTrue(filled($user->fresh()->getAppAuthenticationRecoveryCodes()));
    }

    public function test_disabling_mfa_with_an_incorrect_password_is_rejected(): void
    {
        $provider = Arr::first(Filament::getCurrentOrDefaultPanel()->getMultiFactorAuthenticationProviders());
        $user = $this->makeUserWithMfa();

        try {
            $component = livewire(EditProfile::class)
                ->callAction(
                    TestAction::make('disableAppAuthentication')->schemaComponent('app', schema: 'content'),
                    ['code' => $provider->getCurrentCode($user), 'password' => 'not-the-password'],
                );

            $this->assertComponentDidNotCrash($component, 'the request to turn off the second factor');
        } catch (\PHPUnit\Framework\AssertionFailedError $e) {
            throw $e;
        } catch (\Throwable $e) {
            $this->assertExceptionIsRefusal($e, 'the request to turn off the second factor');
        }

        $this->assertTrue(filled($user->fresh()->getAppAuthenticationSecret()));
        $this->assertTrue(filled($user->fresh()->getAppAuthenticationRecoveryCodes()));
    }
}
