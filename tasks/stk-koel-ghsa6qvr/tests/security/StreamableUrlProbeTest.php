<?php

namespace Tests\Hidden;

use App\Services\Podcast\PodcastService;
use GuzzleHttp\Psr7\Response;
use PHPUnit\Framework\Attributes\Test;
use Throwable;

class StreamableUrlProbeTest extends HiddenTestCase
{
    #[Test]
    public function doesNotProbeAnInternalAddress(): void
    {
        $client = new RecordingClient([new Response(200, ['Access-Control-Allow-Origin' => '*'])]);

        try {
            app(PodcastService::class)->getStreamableUrl('http://127.0.0.1:6379/INFO', $client->client);
        } catch (Throwable) {
            // a refusal is fine; the point is that nothing was requested
        }

        self::assertFalse($client->contacted('127.0.0.1'));
    }

    #[Test]
    public function doesNotFollowARedirectToAnInternalAddress(): void
    {
        $client = new RecordingClient([
            new Response(302, ['Location' => 'http://127.0.0.1/internal']),
            new Response(200, ['Access-Control-Allow-Origin' => '*']),
        ]);

        try {
            app(PodcastService::class)->getStreamableUrl('https://8.8.8.8/episode.mp3', $client->client);
        } catch (Throwable) {
            // a refusal is fine; the point is that nothing was requested from the target
        }

        self::assertFalse($client->contacted('127.0.0.1'));
    }
}
