<?php

namespace Tests\Hidden;

use App\Ai\AiAssistantResult;
use App\Ai\AiRequestContext;
use App\Ai\Tools\AddPodcast;
use App\Models\Podcast;
use GuzzleHttp\Psr7\Response;
use Laravel\Ai\Tools\Request;
use PHPUnit\Framework\Attributes\Test;
use Psr\Http\Client\ClientInterface;
use Throwable;

use function Tests\create_user;

class AssistantPodcastToolTest extends HiddenTestCase
{
    #[Test]
    public function doesNotFetchAFeedFromAnInternalAddress(): void
    {
        $client = new RecordingClient([new Response(200, [], Feeds::one('http://127.0.0.1/secret.mp3'))]);
        $this->instance(ClientInterface::class, $client->client);

        $user = create_user();
        $tool = new AddPodcast(
            new AiRequestContext($user),
            new AiAssistantResult(),
            app(\App\Services\Podcast\PodcastService::class),
        );

        try {
            $tool->handle(new Request(['url' => 'http://127.0.0.1/feed.xml']));
        } catch (Throwable) {
            // a refusal is fine; the point is that nothing was requested
        }

        self::assertFalse($client->contacted('127.0.0.1'));
        $this->assertDatabaseMissing(Podcast::class, ['url' => 'http://127.0.0.1/feed.xml']);
    }
}
