<?php

namespace CweTests\Functional;

use CweTests\TestCase;
use Filament\Actions\Testing\TestAction;
use Filament\Auth\Pages\EditProfile;
use Filament\Facades\Filament;
use Filament\Tests\Fixtures\Models\User;
use Illuminate\Support\Arr;

use function Filament\Tests\livewire;

/**
 * The account holder must still be able to disable app-based multi-factor
 * authentication when they supply a valid one-time code (and, where required,
 * their current password).
 */
class LegitimateManagementTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Filament::setCurrentPanel('app-authentication');
    }

    public function test_user_can_disable_mfa_with_a_valid_code_and_password(): void
    {
        $provider = Arr::first(Filament::getCurrentOrDefaultPanel()->getMultiFactorAuthenticationProviders());
        $user = User::factory()->hasAppAuthentication($provider->generateRecoveryCodes())->create();
        $this->actingAs($user);

        $this->assertTrue(filled($user->getAppAuthenticationSecret()));

        livewire(EditProfile::class)
            ->callAction(
                TestAction::make('disableAppAuthentication')->schemaComponent('app', schema: 'content'),
                ['code' => $provider->getCurrentCode($user), 'password' => 'password'],
            )
            ->assertHasNoFormErrors();

        $this->assertTrue(blank($user->fresh()->getAppAuthenticationSecret()));
    }
}
