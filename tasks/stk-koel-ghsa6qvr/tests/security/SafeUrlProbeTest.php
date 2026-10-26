<?php

namespace Tests\Hidden;

use App\Models\RadioStation;
use Illuminate\Support\Facades\Http;
use PHPUnit\Framework\Attributes\Test;

use function Tests\create_user;

class SafeUrlProbeTest extends HiddenTestCase
{
    #[Test]
    public function doesNotContactARedirectTargetOnAnInternalAddress(): void
    {
        Http::fake([
            '8.8.8.8/*' => Http::response('', 302, ['Location' => 'http://127.0.0.1/admin']),
            '*' => Http::response('', 200, ['Content-Type' => 'audio/mpeg']),
        ]);

        $user = create_user();

        $response = $this->postAs('/api/radio/stations', [
            'url' => 'https://8.8.8.8/stream',
            'name' => 'Redirect attempt',
        ], $user);

        $this->assertClientError($response->getStatusCode());
        self::assertSame([], $this->httpRequestsTo('127.0.0.1'));
        $this->assertDatabaseMissing(RadioStation::class, ['url' => 'https://8.8.8.8/stream']);
    }
}
