<?php

namespace CraftTask\Harness;

use Craft;
use craft\services\Plugins;

/**
 * Answers the plugin-installation call the way a real plugin would: it writes the response headers
 * the product reads after installation. Everything below the service call is the real controller.
 */
final class PluginInstallStub extends Plugins
{
    public function __construct(
        private ?string $headerName = null,
        private ?string $headerValue = null,
    ) {
        parent::__construct([]);
    }

    public function installPlugin(string $handle, ?string $edition = null): bool
    {
        if ($this->headerName !== null && $this->headerValue !== null) {
            Craft::$app->getResponse()->getHeaders()->set($this->headerName, $this->headerValue);
        }
        return true;
    }
}
