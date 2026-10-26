<?php

namespace Tests\Hidden;

use App\Models\Song;
use App\Values\Podcast\EpisodePlayable;
use GuzzleHttp\Psr7\Response;
use Illuminate\Support\Facades\Http;
use PHPUnit\Framework\Attributes\Test;
use Psr\Http\Client\ClientInterface;
use Throwable;

use function Tests\create_user;

class PodcastEpisodeEnclosureTest extends HiddenTestCase
{
    #[Test]
    public function doesNotDownloadEpisodeMediaFromAnInternalAddress(): void
    {
        Http::fake(['*' => Http::response('INTERNAL-SECRET')]);

        $episode = Song::factory()->asEpisode()->createOne(['path' => 'http://127.0.0.1:6379/INFO']);

        try {
            EpisodePlayable::getForEpisode($episode);
        } catch (Throwable) {
        }

        self::assertSame([], $this->httpRequestsTo('127.0.0.1'));
    }

    #[Test]
    public function doesNotFollowARedirectToAnInternalAddress(): void
    {
        Http::fake([
            '8.8.8.8/*' => Http::response('', 302, ['Location' => 'http://127.0.0.1/internal']),
            '*' => Http::response('INTERNAL-SECRET'),
        ]);

        $episode = Song::factory()->asEpisode()->createOne(['path' => 'https://8.8.8.8/episode.mp3']);

        try {
            EpisodePlayable::getForEpisode($episode);
        } catch (Throwable) {
        }

        self::assertSame([], $this->httpRequestsTo('127.0.0.1'));
    }

    #[Test]
    public function doesNotStoreAnEpisodePointingAtAnInternalAddress(): void
    {
        $client = new RecordingClient([
            new Response(200, [], Feeds::mixed('https://8.8.8.8/public.mp3', 'http://127.0.0.1:6379/INFO')),
        ]);
        $this->instance(ClientInterface::class, $client->client);

        $user = create_user();
        $this->postAs('/api/podcasts', ['url' => 'https://8.8.8.8/feed.xml'], $user);

        self::assertSame(
            0,
            Song::query()->where('path', 'http://127.0.0.1:6379/INFO')->count(),
        );
    }

    #[Test]
    public function doesNotStoreAnEpisodePointingAtALinkLocalAddress(): void
    {
        $client = new RecordingClient([
            new Response(200, [], Feeds::mixed('https://8.8.8.8/public.mp3', 'http://169.254.169.254/latest/meta-data/')),
        ]);
        $this->instance(ClientInterface::class, $client->client);

        $user = create_user();
        $this->postAs('/api/podcasts', ['url' => 'https://8.8.8.8/feed.xml'], $user);

        self::assertSame(
            0,
            Song::query()->where('path', 'http://169.254.169.254/latest/meta-data/')->count(),
        );
    }
}
