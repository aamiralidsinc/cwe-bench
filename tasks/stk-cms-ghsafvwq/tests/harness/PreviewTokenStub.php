<?php

namespace CraftTask\Harness;

use craft\services\Tokens;

/**
 * Answers the preview-token call without a database. The redirect decision happens after this call
 * and is entirely the product's own code.
 */
final class PreviewTokenStub extends Tokens
{
    public function __construct(private string $token = 'task-preview-token')
    {
        parent::__construct([]);
    }

    public function createPreviewToken(mixed $route, ?int $usageLimit = null, ?string $token = null): string|false
    {
        return $this->token;
    }
}
