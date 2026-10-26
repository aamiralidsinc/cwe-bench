<?php

namespace Tests\Hidden;

use App\Models\RadioStation;
use Illuminate\Support\Facades\Http;
use PHPUnit\Framework\Attributes\Test;

use function Tests\create_user;

class RadioIntakeFlowTest extends HiddenTestCase
{
    #[Test]
    public function acceptsAPublicRadioStation(): void
    {
        Http::fake(['*' => Http::response('', 200, ['Content-Type' => 'audio/mpeg'])]);

        $user = create_user();

        $this->postAs('/api/radio/stations', [
            'url' => 'https://8.8.8.8/stream',
            'name' => 'Public Station',
            'is_public' => true,
            'description' => 'A station on the public internet.',
        ], $user)->assertCreated();

        $this->assertDatabaseHas(RadioStation::class, [
            'url' => 'https://8.8.8.8/stream',
            'name' => 'Public Station',
            'is_public' => true,
            'user_id' => $user->id,
        ]);
    }
}
