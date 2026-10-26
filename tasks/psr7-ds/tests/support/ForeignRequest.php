<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Support;

use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\StreamInterface;
use Psr\Http\Message\UriInterface;

/**
 * A minimal request implementation owned by the caller, not by the library under test.
 */
final class ForeignRequest implements RequestInterface
{
    private string $method;
    private UriInterface $uri;
    private string $requestTarget;
    /** @var array<string, array{0: string, 1: string[]}> */
    private array $headers = [];
    private StreamInterface $body;
    private string $protocol = '1.1';

    /** @param array<string, string|string[]> $headers */
    public function __construct(string $method, UriInterface $uri, array $headers = [], ?StreamInterface $body = null)
    {
        $this->method = $method;
        $this->uri = $uri;
        $this->requestTarget = $uri->getPath() === '' ? '/' : $uri->getPath();
        $this->body = $body ?? new TestStream();
        foreach ($headers as $name => $value) {
            $this->headers[strtolower($name)] = [$name, is_array($value) ? array_values($value) : [(string) $value]];
        }
    }

    public function getProtocolVersion(): string
    {
        return $this->protocol;
    }

    public function withProtocolVersion(string $version): self
    {
        $new = clone $this;
        $new->protocol = $version;

        return $new;
    }

    public function getHeaders(): array
    {
        $headers = [];
        foreach ($this->headers as [$name, $values]) {
            $headers[$name] = $values;
        }

        return $headers;
    }

    public function hasHeader(string $name): bool
    {
        return isset($this->headers[strtolower($name)]);
    }

    public function getHeader(string $name): array
    {
        return $this->headers[strtolower($name)][1] ?? [];
    }

    public function getHeaderLine(string $name): string
    {
        return implode(', ', $this->getHeader($name));
    }

    public function withHeader(string $name, $value): self
    {
        $new = clone $this;
        $new->headers[strtolower($name)] = [$name, is_array($value) ? array_values($value) : [(string) $value]];

        return $new;
    }

    public function withAddedHeader(string $name, $value): self
    {
        $new = clone $this;
        $key = strtolower($name);
        $values = is_array($value) ? array_values($value) : [(string) $value];
        if (isset($new->headers[$key])) {
            $new->headers[$key][1] = array_merge($new->headers[$key][1], $values);
        } else {
            $new->headers[$key] = [$name, $values];
        }

        return $new;
    }

    public function withoutHeader(string $name): self
    {
        $new = clone $this;
        unset($new->headers[strtolower($name)]);

        return $new;
    }

    public function getBody(): StreamInterface
    {
        return $this->body;
    }

    public function withBody(StreamInterface $body): self
    {
        $new = clone $this;
        $new->body = $body;

        return $new;
    }

    public function getRequestTarget(): string
    {
        return $this->requestTarget;
    }

    public function withRequestTarget(string $requestTarget): self
    {
        $new = clone $this;
        $new->requestTarget = $requestTarget;

        return $new;
    }

    public function getMethod(): string
    {
        return $this->method;
    }

    public function withMethod(string $method): self
    {
        $new = clone $this;
        $new->method = $method;

        return $new;
    }

    public function getUri(): UriInterface
    {
        return $this->uri;
    }

    public function withUri(UriInterface $uri, bool $preserveHost = false): self
    {
        $new = clone $this;
        $new->uri = $uri;
        if (!$preserveHost || !$new->hasHeader('Host')) {
            $host = $uri->getHost();
            if ($host !== '') {
                if ($uri->getPort() !== null) {
                    $host .= ':'.$uri->getPort();
                }
                $new = $new->withHeader('Host', $host);
            }
        }

        return $new;
    }
}
