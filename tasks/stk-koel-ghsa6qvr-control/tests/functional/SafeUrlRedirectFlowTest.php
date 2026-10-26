<?php

namespace Tests\Hidden;

use App\Models\RadioStation;
use Illuminate\Support\Facades\Http;
use PHPUnit\Framework\Attributes\Test;

use function Tests\create_user;

class SafeUrlRedirectFlowTest extends HiddenTestCase
{
    #[Test]
    public function acceptsARedirectBetweenPublicAddresses(): void
    {
        Http::fake([
            '8.8.8.8/*' => Http::response('', 302, ['Location' => 'https://1.1.1.1/stream']),
            '1.1.1.1/*' => Http::response('', 200, ['Content-Type' => 'audio/mpeg']),
            '*' => Http::response('', 200, ['Content-Type' => 'audio/mpeg']),
        ]);

        $user = create_user();

        $this->postAs('/api/radio/stations', [
            'url' => 'https://8.8.8.8/stream',
            'name' => 'Redirected Station',
            'is_public' => true,
        ], $user)->assertCreated();

        $this->assertDatabaseHas(RadioStation::class, [
            'url' => 'https://8.8.8.8/stream',
            'user_id' => $user->id,
        ]);
    }
}
