<?php

namespace Tests\Hidden;

use App\Services\Podcast\PodcastService;
use GuzzleHttp\Psr7\Response;
use PHPUnit\Framework\Attributes\Test;

class StreamableUrlFlowTest extends HiddenTestCase
{
    #[Test]
    public function resolvesAPublicRedirectChain(): void
    {
        $client = new RecordingClient([
            new Response(302, ['Location' => 'https://1.1.1.1/final.mp3']),
            new Response(200, ['Access-Control-Allow-Origin' => '*']),
        ]);

        $url = app(PodcastService::class)->getStreamableUrl(
            'https://8.8.8.8/episode.mp3',
            $client->client,
        );

        self::assertSame('https://1.1.1.1/final.mp3', $url);
    }
}
