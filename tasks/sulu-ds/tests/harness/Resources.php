<?php

namespace Sulu\Task\Harness;

final class Resources
{
    public static function id(string $webspace, string $name): string
    {
        return 'page-' . $webspace . '-' . $name;
    }

    public static function webspaceFor(string $resourceId): ?string
    {
        if (\preg_match('/^page-([a-z0-9_]+)-/', $resourceId, $matches)) {
            return $matches[1];
        }

        return null;
    }
}
