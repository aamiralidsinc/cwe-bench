<?php

namespace Tests\Hidden;

use App\Ai\AiAssistantResult;
use App\Ai\AiRequestContext;
use App\Ai\Tools\AddPodcast;
use App\Ai\Tools\AddRadioStation;
use App\Models\Podcast;
use App\Models\RadioStation;
use App\Services\Podcast\PodcastService;
use App\Services\RadioService;
use GuzzleHttp\Psr7\Response;
use Illuminate\Support\Facades\Http;
use Laravel\Ai\Tools\Request;
use PHPUnit\Framework\Attributes\Test;
use Psr\Http\Client\ClientInterface;

use function Tests\create_user;

class AssistantToolsFlowTest extends HiddenTestCase
{
    #[Test]
    public function addsAPublicRadioStation(): void
    {
        Http::fake(['*' => Http::response('', 200, ['Content-Type' => 'audio/mpeg'])]);

        $user = create_user();
        $tool = new AddRadioStation(
            new AiRequestContext($user),
            new AiAssistantResult(),
            app(RadioService::class),
        );

        $tool->handle(new Request(['name' => 'Public Radio', 'url' => 'https://8.8.8.8/stream']));

        $this->assertDatabaseHas(RadioStation::class, [
            'url' => 'https://8.8.8.8/stream',
            'user_id' => $user->id,
        ]);
    }

    #[Test]
    public function subscribesToAPublicFeed(): void
    {
        $client = new RecordingClient([new Response(200, [], Feeds::one('https://8.8.8.8/episode.mp3'))]);
        $this->instance(ClientInterface::class, $client->client);

        $user = create_user();
        $tool = new AddPodcast(
            new AiRequestContext($user),
            new AiAssistantResult(),
            app(PodcastService::class),
        );

        $tool->handle(new Request(['url' => 'https://8.8.8.8/feed.xml']));

        $this->assertDatabaseHas(Podcast::class, ['url' => 'https://8.8.8.8/feed.xml']);
    }
}
