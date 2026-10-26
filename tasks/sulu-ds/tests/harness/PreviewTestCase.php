<?php

namespace Sulu\Task\Harness;

use PHPUnit\Framework\TestCase;
use Sulu\Bundle\PreviewBundle\Domain\Model\PreviewLinkInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Core\Authentication\Token\UsernamePasswordToken;

abstract class PreviewTestCase extends TestCase
{
    protected static ?TestKernel $kernel = null;
    protected static ?ContainerInterface $container = null;

    public static function setUpBeforeClass(): void
    {
        if (null === self::$kernel) {
            self::$kernel = new TestKernel('test', true);
            self::$kernel->boot();
        }
        self::$container = self::$kernel->getContainer();
        self::repository()->clear();
        self::service('sulu_activity.domain_event_collector')->clear();
    }

    protected static function service(string $id): object
    {
        return self::$container->get('test.service_container')->get($id);
    }

    protected static function repository(): InMemoryPreviewLinkRepository
    {
        /** @var InMemoryPreviewLinkRepository $repository */
        $repository = self::service('sulu_preview.preview_link_repository');

        return $repository;
    }

    protected function actAs(string $identifier): void
    {
        $user = new TestUser(1, $identifier);
        $constructor = new \ReflectionMethod(UsernamePasswordToken::class, '__construct');
        $token = $constructor->getNumberOfParameters() >= 4
            ? new UsernamePasswordToken($user, null, 'main', ['ROLE_USER'])
            : new UsernamePasswordToken($user, 'main', ['ROLE_USER']);

        self::service('security.token_storage')->setToken($token);
    }

    protected function http(string $method, string $uri, string $actor): Response
    {
        $this->actAs($actor);

        return self::$kernel->handle(Request::create($uri, $method));
    }

    protected function createLink(
        string $resourceKey,
        string $resourceId,
        string $locale = 'en',
        array $options = []
    ): PreviewLinkInterface {
        $repository = self::repository();
        $previewLink = $repository->create($resourceKey, $resourceId, $locale, $options);
        $repository->add($previewLink);
        $repository->commit();

        return $previewLink;
    }

    protected static function assertClientError(Response $response): void
    {
        self::assertGreaterThanOrEqual(400, $response->getStatusCode(), 'expected a client error');
        self::assertLessThan(500, $response->getStatusCode(), 'expected a client error, not a server error');
    }
}
