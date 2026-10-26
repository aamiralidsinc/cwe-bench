<?php

namespace Sulu\Task\Harness;

final class PermissionMap
{
    /**
     * @var array<string, array<string, string[]>>
     */
    private const USERS = [
        'attacker' => [],
        'viewer_alpha' => ['sulu.webspaces.alpha' => ['view']],
        'viewer_beta' => ['sulu.webspaces.beta' => ['view']],
        'editor_alpha' => ['sulu.webspaces.alpha' => ['view', 'add', 'edit', 'delete']],
        'admin' => ['*' => ['view', 'add', 'edit', 'delete', 'security', 'live']],
    ];

    public static function granted(string $user, ?string $context, string $permission): bool
    {
        $contexts = self::USERS[$user] ?? [];
        $permissions = $contexts[$context] ?? $contexts['*'] ?? [];

        return \in_array($permission, $permissions, true);
    }
}
