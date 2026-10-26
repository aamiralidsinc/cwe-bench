<?php

namespace App\Ai\Tools;

use App\Ai\AiAssistantResult;
use App\Ai\AiRequestContext;
use App\Services\Podcast\PodcastService;
use Illuminate\Contracts\JsonSchema\JsonSchema;
use Laravel\Ai\Contracts\Tool;
use Laravel\Ai\Tools\Request;
use Stringable;

class AddPodcast implements Tool
{
    public function __construct(
        private readonly AiRequestContext $context,
        private readonly AiAssistantResult $result,
        private readonly PodcastService $podcastService,
    ) {}

    public function description(): Stringable|string
    {
        return 'Subscribe to a podcast. Use this when the user wants to subscribe to a podcast from an RSS feed URL.';
    }

    public function schema(JsonSchema $schema): array
    {
        return [
            'url' => $schema->string()->required()->description('The RSS feed URL of the podcast'),
        ];
    }

    public function handle(Request $request): Stringable|string
    {
        $podcast = $this->podcastService->addPodcast($request['url'], $this->context->user);

        $this->result->action = 'add_podcast';
        $this->result->data = [
            'podcast' => $podcast,
        ];

        return sprintf('Podcast "%s" added successfully.', $podcast->title);
    }
}
