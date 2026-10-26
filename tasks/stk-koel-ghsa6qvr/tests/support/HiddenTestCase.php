<?php

namespace Tests\Hidden;

use Illuminate\Support\Facades\Http;
use Tests\TestCase;

abstract class HiddenTestCase extends TestCase
{
    private bool $httpWrapperReplaced = false;

    /** @param array<string, string> $bodies */
    protected function useFakeHttpStream(array $bodies = []): void
    {
        FakeHttpStream::reset($bodies);

        if (in_array('http', stream_get_wrappers(), true)) {
            stream_wrapper_unregister('http');
        }

        stream_wrapper_register('http', FakeHttpStream::class);
        $this->httpWrapperReplaced = true;
    }

    private function restoreHttpStream(): void
    {
        if (!$this->httpWrapperReplaced) {
            return;
        }

        if (in_array('http', stream_get_wrappers(), true)) {
            stream_wrapper_unregister('http');
        }

        stream_wrapper_restore('http');
        $this->httpWrapperReplaced = false;
    }

    protected function tearDown(): void
    {
        $this->restoreHttpStream();

        parent::tearDown();
    }

    /** @return list<string> */
    protected function httpRequestsTo(string $needle): array
    {
        return Http::recorded()
            ->map(static fn (array $pair): string => $pair[0]->url())
            ->filter(static fn (string $url): bool => str_contains($url, $needle))
            ->values()
            ->all();
    }

    protected function assertClientError(int $status): void
    {
        self::assertTrue(
            $status >= 400 && $status < 500,
            sprintf('expected the request to be refused with a client error, got HTTP %d', $status),
        );
    }
}
