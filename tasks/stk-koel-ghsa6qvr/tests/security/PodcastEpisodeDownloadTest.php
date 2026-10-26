<?php

namespace Tests\Hidden;

use App\Models\Song;
use App\Values\Podcast\EpisodePlayable;
use Illuminate\Support\Facades\Http;
use PHPUnit\Framework\Attributes\Test;
use Throwable;

class PodcastEpisodeDownloadTest extends HiddenTestCase
{
    #[Test]
    public function doesNotFetchMediaFromAnInternalAddress(): void
    {
        Http::fake(['*' => Http::response('INTERNAL-SECRET')]);

        $episode = Song::factory()->asEpisode()->createOne([
            'path' => 'http://127.0.0.1:6379/INFO',
        ]);

        try {
            EpisodePlayable::getForEpisode($episode);
        } catch (Throwable) {
            // a refusal is fine; the point is that nothing was requested
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

        $episode = Song::factory()->asEpisode()->createOne([
            'path' => 'https://8.8.8.8/episode.mp3',
        ]);

        try {
            EpisodePlayable::getForEpisode($episode);
        } catch (Throwable) {
            // a refusal is fine; the point is that nothing was requested from the target
        }

        self::assertSame([], $this->httpRequestsTo('127.0.0.1'));
    }
}
