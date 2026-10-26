<?php

namespace Sulu\Task\Harness;

use Symfony\Component\Config\FileLocator;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Extension\Extension;
use Symfony\Component\DependencyInjection\Loader\PhpFileLoader;
use Symfony\Component\DependencyInjection\Reference;
use Symfony\Component\Security\Core\Authentication\Token\Storage\TokenStorage;
use Sulu\Component\Security\Authorization\SecurityChecker;

class TestPreviewExtension extends Extension
{
    private const PRODUCT_CONFIG = '/workspace/src/Sulu/Bundle/PreviewBundle/Resources/config';

    public function load(array $configs, ContainerBuilder $container): void
    {
        $container->setParameter('sulu_preview.mode', 'auto');
        $container->setParameter('sulu_preview.delay', 500);

        // Load the product's real service definitions: the task must exercise the wiring the fix
        // needs, not a copy of it.
        $loader = new PhpFileLoader($container, new FileLocator(self::PRODUCT_CONFIG));
        $loader->load('services.php');

        // Services whose infrastructure (webspace manager, route defaults provider, preview kernel,
        // doctrine) is not part of this offline harness.
        foreach ([
            'sulu_preview.admin',
            'sulu_preview.cache_command_subscriber',
            'sulu_preview.preview.kernel_factory',
            'sulu_preview.preview.renderer',
            'sulu_preview.preview',
            'sulu_preview.preview_controller',
        ] as $id) {
            if ($container->hasDefinition($id)) {
                $container->removeDefinition($id);
            }
        }

        $container->register('sulu_preview.preview_link_repository', InMemoryPreviewLinkRepository::class)
            ->setPublic(true);

        $container->register('sulu_preview.preview.cache', \Symfony\Component\Cache\Adapter\ArrayAdapter::class)
            ->setPublic(true);

        $container->register('sulu_preview.preview.renderer', TestRenderer::class)
            ->setPublic(true);

        $container->register('sulu_activity.domain_event_collector', TestDomainEventCollector::class)
            ->setPublic(true);

        $container->register('fos_rest.view_handler', TestViewHandler::class)
            ->setPublic(true);

        $container->register('twig', TestTwig::class)
            ->setPublic(true);

        $container->register('security.token_storage', TokenStorage::class)
            ->setPublic(true);

        $container->register('security.authorization_checker', TestAuthorizationChecker::class)
            ->setArguments([new Reference('security.token_storage')])
            ->setPublic(true);

        $container->register('sulu_security.security_checker', SecurityChecker::class)
            ->setArguments([
                new Reference('security.token_storage'),
                new Reference('security.authorization_checker'),
            ])
            ->setPublic(true);

        $container->register('task.access_denied_listener', AccessDeniedListener::class)
            ->addTag('kernel.event_subscriber');

        $container->register('task.preview_provider.pages', TestPreviewObjectProvider::class)
            ->setArguments(['pages'])
            ->addTag('sulu_preview.object_provider', ['provider-key' => 'pages']);

        $container->register('task.preview_provider.media', TestPreviewObjectProvider::class)
            ->setArguments(['media'])
            ->addTag('sulu_preview.object_provider', ['provider-key' => 'media']);
    }
}
