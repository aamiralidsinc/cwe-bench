<?php

namespace CweTests\Functional;

use CweTests\TestCase;
use CweTests\UploadFixtureComponent;
use Filament\Facades\Filament;

use function Filament\Tests\livewire;

/**
 * Legitimate file uploads must keep working: on a component that really does expose
 * a file-upload field, the temporary-file-upload endpoints must still accept an
 * upload targeting that field.
 */
class LegitimateUploadTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Filament::setCurrentPanel('app-authentication');
    }

    public function test_upload_to_a_real_file_field_is_allowed(): void
    {
        livewire(UploadFixtureComponent::class)
            ->call('_startUpload', 'data.photo', [['name' => 'a.jpg', 'size' => 1024, 'type' => 'image/jpeg']], false)
            ->assertDispatched('upload:generatedSignedUrl');
    }

    public function test_finish_upload_to_a_real_file_field_is_allowed(): void
    {
        livewire(UploadFixtureComponent::class)
            ->call('_finishUpload', 'data.photo', ['livewire-tmp/legitimate.jpg'], false)
            ->assertDispatched('upload:finished');
    }
}
