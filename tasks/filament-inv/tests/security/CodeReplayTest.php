<?php

namespace CweTests\Security;

use CweTests\TestCase;
use Filament\Auth\Pages\Login;
use Filament\Facades\Filament;
use Filament\Tests\Fixtures\Models\User;
use Illuminate\Support\Arr;
use Illuminate\Support\Facades\Auth;
use PragmaRX\Google2FAQRCode\Google2FA;

use function Filament\Tests\livewire;

/**
 * A one-time code must be single-use in the sense required by TOTP: once a code is
 * accepted, that code AND every earlier code in the acceptance window must be
 * rejected. Otherwise an attacker who captured a code can keep replaying it for the
 * rest of its window, even after the legitimate user has already signed in with a
 * newer one.
 */
class CodeReplayTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Filament::setCurrentPanel('app-authentication');
    }

    public function test_earlier_code_is_rejected_after_a_newer_code_is_used(): void
    {
        $provider = Arr::first(Filament::getCurrentOrDefaultPanel()->getMultiFactorAuthenticationProviders());
        $user = User::factory()->hasAppAuthentication()->create();
        Auth::login($user);

        $secret = $provider->getSecret($user);
        $google2FA = app(Google2FA::class);

        $timestamp = $google2FA->getTimestamp();
        $earlierCode = $google2FA->oathTotp($secret, $timestamp - 4);
        $currentCode = $google2FA->oathTotp($secret, $timestamp);

        // The newer code is accepted once.
        $this->assertTrue($provider->verifyCode($currentCode, $secret, shouldPreventCodeReuse: true));

        // The earlier (still in-window) code must now be rejected.
        $this->assertFalse($provider->verifyCode($earlierCode, $secret, shouldPreventCodeReuse: true));

        Auth::logout();
    }

    public function test_captured_earlier_code_cannot_sign_in_after_the_user_used_a_newer_one(): void
    {
        $provider = Arr::first(Filament::getCurrentOrDefaultPanel()->getMultiFactorAuthenticationProviders());
        $id = $provider->getId();
        $user = User::factory()->hasAppAuthentication()->create();

        $secret = $provider->getSecret($user);
        $google2FA = app(Google2FA::class);
        $timestamp = $google2FA->getTimestamp();
        $earlierCode = $google2FA->oathTotp($secret, $timestamp - 4);
        $currentCode = $google2FA->oathTotp($secret, $timestamp);

        // The legitimate user signs in with the current code.
        livewire(Login::class)
            ->fillForm(['email' => $user->email, 'password' => 'password'])
            ->call('authenticate')
            ->fillForm([$id => ['code' => $currentCode]], 'multiFactorChallengeForm')
            ->call('authenticate')
            ->assertRedirect(Filament::getUrl());
        $this->assertAuthenticatedAs($user);

        // A fresh (attacker) session replays the captured earlier code.
        Auth::logout();

        livewire(Login::class)
            ->fillForm(['email' => $user->email, 'password' => 'password'])
            ->call('authenticate')
            ->fillForm([$id => ['code' => $earlierCode]], 'multiFactorChallengeForm')
            ->call('authenticate')
            ->assertNoRedirect();

        $this->assertGuest();
    }
}
