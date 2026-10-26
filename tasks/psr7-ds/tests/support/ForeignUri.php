<?php

declare(strict_types=1);

namespace CweBench\Psr7Tests\Support;

use Psr\Http\Message\UriInterface;

/**
 * A minimal URI implementation owned by the caller, not by the library under test.
 */
final class ForeignUri implements UriInterface
{
    private string $scheme = '';
    private string $userInfo = '';
    private string $host = '';
    private ?int $port = null;
    private string $path = '';
    private string $query = '';
    private string $fragment = '';

    /** @param array<string, mixed> $parts */
    public function __construct(array $parts = [])
    {
        $this->scheme = (string) ($parts['scheme'] ?? '');
        $this->userInfo = (string) ($parts['userInfo'] ?? '');
        $this->host = (string) ($parts['host'] ?? '');
        $this->port = isset($parts['port']) ? (int) $parts['port'] : null;
        $this->path = (string) ($parts['path'] ?? '');
        $this->query = (string) ($parts['query'] ?? '');
        $this->fragment = (string) ($parts['fragment'] ?? '');
    }

    public function getScheme(): string
    {
        return $this->scheme;
    }

    public function getAuthority(): string
    {
        $authority = $this->host;
        if ($this->userInfo !== '') {
            $authority = $this->userInfo.'@'.$authority;
        }
        if ($this->port !== null) {
            $authority .= ':'.$this->port;
        }

        return $authority;
    }

    public function getUserInfo(): string
    {
        return $this->userInfo;
    }

    public function getHost(): string
    {
        return $this->host;
    }

    public function getPort(): ?int
    {
        return $this->port;
    }

    public function getPath(): string
    {
        return $this->path;
    }

    public function getQuery(): string
    {
        return $this->query;
    }

    public function getFragment(): string
    {
        return $this->fragment;
    }

    public function withScheme($scheme): UriInterface
    {
        $new = clone $this;
        $new->scheme = (string) $scheme;

        return $new;
    }

    public function withUserInfo($user, $password = null): UriInterface
    {
        $new = clone $this;
        $new->userInfo = (string) $user.($password !== null ? ':'.$password : '');

        return $new;
    }

    public function withHost($host): UriInterface
    {
        $new = clone $this;
        $new->host = (string) $host;

        return $new;
    }

    public function withPort($port): UriInterface
    {
        $new = clone $this;
        $new->port = $port !== null ? (int) $port : null;

        return $new;
    }

    public function withPath($path): UriInterface
    {
        $new = clone $this;
        $new->path = (string) $path;

        return $new;
    }

    public function withQuery($query): UriInterface
    {
        $new = clone $this;
        $new->query = (string) $query;

        return $new;
    }

    public function withFragment($fragment): UriInterface
    {
        $new = clone $this;
        $new->fragment = (string) $fragment;

        return $new;
    }

    public function __toString(): string
    {
        $uri = '';
        if ($this->scheme !== '') {
            $uri .= $this->scheme.':';
        }
        if ($this->getAuthority() !== '') {
            $uri .= '//'.$this->getAuthority();
        }
        $uri .= $this->path;
        if ($this->query !== '') {
            $uri .= '?'.$this->query;
        }
        if ($this->fragment !== '') {
            $uri .= '#'.$this->fragment;
        }

        return $uri;
    }
}
