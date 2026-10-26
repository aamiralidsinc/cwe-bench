<?php

namespace Tests\Hidden;

use GuzzleHttp\Client;
use GuzzleHttp\Handler\MockHandler;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Middleware;
use GuzzleHttp\Psr7\Response;
use Psr\Http\Message\RequestInterface;

/**
 * A Guzzle client that serves canned responses and records every request it is asked to send,
 * including requests the redirect middleware would normally follow.
 */
final class RecordingClient
{
    /** @var list<array{request: RequestInterface}> */
    public array $history = [];

    public Client $client;

    /** @param list<Response> $responses */
    public function __construct(array $responses)
    {
        $stack = HandlerStack::create(new MockHandler($responses));
        $stack->push(Middleware::history($this->history));
        $this->client = new Client(['handler' => $stack]);
    }

    /** @return list<string> */
    public function urls(): array
    {
        return array_map(
            static fn (array $entry): string => (string) $entry['request']->getUri(),
            $this->history,
        );
    }

    public function contacted(string $needle): bool
    {
        foreach ($this->urls() as $url) {
            if (str_contains($url, $needle)) {
                return true;
            }
        }

        return false;
    }
}
