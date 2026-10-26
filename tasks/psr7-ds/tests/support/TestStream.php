<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Support;

use Psr\Http\Message\StreamInterface;

/**
 * A minimal read-only stream owned by the caller.
 */
final class TestStream implements StreamInterface
{
    private string $contents;
    private int $position = 0;

    public function __construct(string $contents = '')
    {
        $this->contents = $contents;
    }

    public function __toString(): string
    {
        return $this->contents;
    }

    public function close(): void
    {
    }

    public function detach()
    {
        return null;
    }

    public function getSize(): ?int
    {
        return strlen($this->contents);
    }

    public function tell(): int
    {
        return $this->position;
    }

    public function eof(): bool
    {
        return $this->position >= strlen($this->contents);
    }

    public function isSeekable(): bool
    {
        return true;
    }

    public function seek($offset, $whence = SEEK_SET): void
    {
        $this->position = (int) $offset;
    }

    public function rewind(): void
    {
        $this->position = 0;
    }

    public function isWritable(): bool
    {
        return false;
    }

    public function write($string): int
    {
        return 0;
    }

    public function isReadable(): bool
    {
        return true;
    }

    public function read($length): string
    {
        $chunk = substr($this->contents, $this->position, (int) $length);
        $this->position += strlen($chunk);

        return $chunk;
    }

    public function getContents(): string
    {
        $rest = substr($this->contents, $this->position);
        $this->position = strlen($this->contents);

        return $rest;
    }

    public function getMetadata($key = null)
    {
        return $key === null ? [] : null;
    }
}
