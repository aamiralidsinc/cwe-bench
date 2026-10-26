<?php

namespace Sulu\Task\Harness;

use Symfony\Component\DependencyInjection\Extension\ExtensionInterface;
use Symfony\Component\HttpKernel\Bundle\Bundle;

class TestPreviewBundle extends Bundle
{
    public function getContainerExtension(): ?ExtensionInterface
    {
        return new TestPreviewExtension();
    }
}
