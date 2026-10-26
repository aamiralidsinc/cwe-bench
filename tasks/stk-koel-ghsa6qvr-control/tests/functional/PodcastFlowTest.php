<?php

namespace Tests\Hidden;

use App\Models\Podcast;
use App\Values\Podcast\EpisodePlayable;
use GuzzleHttp\Psr7\Response;
use Illuminate\Support\Facades\Http;
use PHPUnit\Framework\Attributes\Test;
use Psr\Http\Client\ClientInterface;

use function Tests\create_user;

class PodcastFlowTest extends HiddenTestCase
{
    #[Test]
    public function subscribesToAPublicFeedAndDownloadsPublicMedia(): void
    {
        Http::fake([
            '8.8.8.8/feed.xml' => Http::response('', 200),
            '8.8.8.8/episode.mp3' => Http::response('PUBLIC-AUDIO'),
            '*' => Http::response('', 200),
        ]);

        $client = new RecordingClient([new Response(200, [], Feeds::one('https://8.8.8.8/episode.mp3'))]);
        $this->instance(ClientInterface::class, $client->client);

        $user = create_user();

        $this->postAs('/api/podcasts', ['url' => 'https://8.8.8.8/feed.xml'], $user)->assertCreated();

        $podcast = Podcast::query()->firstWhere('url', 'https://8.8.8.8/feed.xml');
        self::assertNotNull($podcast);
        self::assertCount(1, $podcast->episodes);

        $episode = $podcast->episodes->first();
        self::assertSame('https://8.8.8.8/episode.mp3', $episode->path);

        $playable = EpisodePlayable::getForEpisode($episode);
        self::assertSame(md5('PUBLIC-AUDIO'), $playable->checksum);
        self::assertNotSame([], $this->httpRequestsTo('8.8.8.8/episode.mp3'));
    }
}
