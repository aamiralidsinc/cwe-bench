<?php

namespace CweTests\Security;

use CweTests\AssertsRefusal;
use CweTests\TestCase;
use Filament\Auth\Pages\Login;
use Filament\Facades\Filament;

use function Filament\Tests\livewire;

/**
 * The login page exposes Livewire's temporary-file-upload endpoints even though it
 * has no file-upload field. An unauthenticated visitor must not be able to drive
 * those endpoints to stage arbitrary files in the application's temporary storage.
 *
 * How the request is refused is the fix's choice: any client error (4xx response, or an
 * exception the application answers with a 4xx, e.g. authorization or validation) or a
 * validation error on the component, with no upload side effect. 2026-10-15: the old exact
 * assertForbidden() failed a correct fix. 2026-10-16: "any throwable" counted a crash
 * (TypeError, null dereference, HTTP 500) as a refusal; it no longer does.
 */
class UnauthenticatedUploadTest extends TestCase
{
    use AssertsRefusal;

    protected function setUp(): void
    {
        parent::setUp();
        Filament::setCurrentPanel('app-authentication');
    }

    public function test_start_upload_on_login_page_is_forbidden(): void
    {
        $this->assertGuest();

        $this->assertUploadRefused(
            fn () => livewire(Login::class)
                ->call('_startUpload', 'data.text', [['name' => 'a.jpg', 'size' => 1024, 'type' => 'image/jpeg']], false),
            'data.text',
        );
    }

    public function test_finish_upload_on_login_page_is_forbidden(): void
    {
        $this->assertGuest();

        $this->assertUploadRefused(
            fn () => livewire(Login::class)
                ->call('_finishUpload', 'data.somethingElse', ['livewire-tmp/tampered.jpg'], false),
            'data.somethingElse',
        );
    }

    private function assertUploadRefused(callable $attempt, string $targetPath): void
    {
        try {
            $component = $attempt();
        } catch (\PHPUnit\Framework\AssertionFailedError $e) {
            throw $e;
        } catch (\Throwable $e) {
            // The request died: it must be a refusal (4xx), not a crash. A thrown request
            // leaves no component state behind, so there is no side effect to inspect.
            $this->assertExceptionIsRefusal($e, 'the unauthenticated upload request');

            return;
        }

        $this->assertComponentDidNotCrash($component, 'the unauthenticated upload request');
        $this->assertTrue(
            $this->componentAnsweredWithClientError($component) || $this->componentHasValidationErrors($component),
            'the unauthenticated upload request was accepted (no client error and no validation error)',
        );

        // No side effect: no signed upload URL handed out, no upload completed, nothing
        // attached to the targeted property.
        $component->assertNotDispatched('upload:generatedSignedUrl');
        $component->assertNotDispatched('upload:finished');
        $this->assertFalse(
            is_object($component->get($targetPath)) || (is_array($component->get($targetPath)) && filled($component->get($targetPath))),
            'a file was attached to the targeted property',
        );
    }
}
