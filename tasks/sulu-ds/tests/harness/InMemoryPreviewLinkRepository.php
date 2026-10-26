<?php

namespace Sulu\Task\Harness;

use Sulu\Bundle\PreviewBundle\Domain\Model\PreviewLinkInterface;
use Sulu\Bundle\PreviewBundle\Domain\Repository\PreviewLinkRepositoryInterface;

class InMemoryPreviewLinkRepository implements PreviewLinkRepositoryInterface
{
    /**
     * @var array<string, PreviewLinkInterface>
     */
    private array $links = [];

    public function create(string $resourceKey, string $resourceId, string $locale, array $options): PreviewLinkInterface
    {
        $token = \bin2hex(\random_bytes(8));

        /** @var class-string<PreviewLinkInterface> $className */
        $className = \Sulu\Bundle\PreviewBundle\Domain\Model\PreviewLink::class;

        return $className::create($token, $resourceKey, $resourceId, $locale, $options);
    }

    public function findByResource(string $resourceKey, string $resourceId, string $locale): ?PreviewLinkInterface
    {
        return $this->links[self::key($resourceKey, $resourceId, $locale)] ?? null;
    }

    public function findByToken(string $token): ?PreviewLinkInterface
    {
        foreach ($this->links as $link) {
            if ($link->getToken() === $token) {
                return $link;
            }
        }

        return null;
    }

    public function add(PreviewLinkInterface $previewLink): void
    {
        $this->links[self::key(
            $previewLink->getResourceKey(),
            $previewLink->getResourceId(),
            $previewLink->getLocale()
        )] = $previewLink;
    }

    public function remove(PreviewLinkInterface $previewLink): void
    {
        unset($this->links[self::key(
            $previewLink->getResourceKey(),
            $previewLink->getResourceId(),
            $previewLink->getLocale()
        )]);
    }

    public function commit(): void
    {
    }

    public function clear(): void
    {
        $this->links = [];
    }

    private static function key(string $resourceKey, string $resourceId, string $locale): string
    {
        return $resourceKey . "\0" . $resourceId . "\0" . $locale;
    }
}
