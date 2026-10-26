<?php

namespace Sulu\Task\Harness;

use Symfony\Bundle\FrameworkBundle\FrameworkBundle;
use Symfony\Component\Config\Loader\LoaderInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\HttpKernel\Kernel;

class TestKernel extends Kernel
{
    public function registerBundles(): iterable
    {
        return [
            new FrameworkBundle(),
            new TestPreviewBundle(),
        ];
    }

    public function registerContainerConfiguration(LoaderInterface $loader): void
    {
        $loader->load(function (ContainerBuilder $container): void {
            $container->loadFromExtension('framework', [
                'secret' => 'task',
                'test' => true,
                'default_locale' => 'en',
                'http_method_override' => false,
                'handle_all_throwables' => true,
                'php_errors' => ['log' => false],
                'router' => [
                    'resource' => __DIR__ . '/routes.yaml',
                    'utf8' => true,
                ],
                'cache' => ['app' => 'cache.adapter.array'],
            ]);
        });
    }

    public function getCacheDir(): string
    {
        return \dirname(__DIR__) . '/var/cache/' . $this->environment;
    }

    public function getLogDir(): string
    {
        return \dirname(__DIR__) . '/var/log';
    }
}
