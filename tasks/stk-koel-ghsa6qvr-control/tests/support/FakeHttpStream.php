<?php

namespace Tests\Hidden;

/**
 * Records every URL a wrapped PHP stream opens. Registering this class for the `http` wrapper
 * lets a test observe exactly which addresses the product's stream client tries to reach without
 * touching the network.
 */
final class FakeHttpStream
{
    /** @var list<string> */
    public static array $opened = [];

    /** @var array<string, string> */
    public static array $bodies = [];

    /** @var resource|null */
    public $context;

    private string $body = '';

    private int $pos = 0;

    /** @param array<string, string> $bodies */
    public static function reset(array $bodies = []): void
    {
        self::$opened = [];
        self::$bodies = $bodies;
    }

    /** @return list<string> */
    public static function openedTo(string $needle): array
    {
        return array_values(array_filter(
            self::$opened,
            static fn (string $url): bool => str_contains($url, $needle),
        ));
    }

    public function stream_open(string $path, string $mode, int $options, ?string &$openedPath): bool
    {
        self::$opened[] = $path;
        $this->body = self::$bodies[$path] ?? self::$bodies['*'] ?? '';
        $this->pos = 0;

        return true;
    }

    public function stream_read(int $count): string
    {
        $chunk = substr($this->body, $this->pos, $count);
        $this->pos += strlen($chunk);

        return $chunk;
    }

    public function stream_eof(): bool
    {
        return $this->pos >= strlen($this->body);
    }

    /** @return array<string, int> */
    public function stream_stat(): array
    {
        return [];
    }

    public function stream_close(): void
    {
    }

    public function stream_set_option(int $option, int $arg1, ?int $arg2): bool
    {
        return true;
    }
}
