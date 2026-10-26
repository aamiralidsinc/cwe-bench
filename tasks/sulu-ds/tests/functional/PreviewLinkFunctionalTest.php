<?php

namespace Sulu\Task\Tests\Functional;

use Sulu\Bundle\PreviewBundle\Application\Manager\PreviewLinkManager;
use Sulu\Task\Harness\PreviewTestCase;
use Sulu\Task\Harness\Resources;
use Symfony\Component\HttpFoundation\Response;

class PreviewLinkFunctionalTest extends PreviewTestCase
{
    public function testViewerCanGenerateReadAndRevokeALink(): void
    {
        $resourceId = Resources::id('alpha', 'flow');

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '?action=generate&resourceKey=pages&locale=en',
            'viewer_alpha'
        );
        self::assertSame(Response::HTTP_CREATED, $response->getStatusCode());
        $generated = $this->json($response);
        self::assertIsString($generated['token']);

        $stored = self::repository()->findByResource('pages', $resourceId, 'en');
        self::assertNotNull($stored);
        self::assertSame($generated['token'], $stored->getToken());

        $response = $this->http(
            'GET',
            '/admin/api/preview-links/' . $resourceId . '?resourceKey=pages&locale=en',
            'viewer_alpha'
        );
        self::assertSame(Response::HTTP_OK, $response->getStatusCode());
        self::assertSame($generated['token'], $this->json($response)['token']);

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '?action=revoke&resourceKey=pages&locale=en',
            'viewer_alpha'
        );
        self::assertSame(Response::HTTP_NO_CONTENT, $response->getStatusCode());
        self::assertNull(self::repository()->findByResource('pages', $resourceId, 'en'));
    }

    public function testAdministratorCanGenerateALinkInAnyWebspace(): void
    {
        $resourceId = Resources::id('beta', 'admin');

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '?action=generate&resourceKey=pages&locale=en',
            'admin'
        );

        self::assertSame(Response::HTTP_CREATED, $response->getStatusCode());
        self::assertNotNull(self::repository()->findByResource('pages', $resourceId, 'en'));
    }

    public function testLinkWithoutSecurityContextKeepsWorking(): void
    {
        $resourceId = 'media-without-security-context';

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '?action=generate&resourceKey=media&locale=en',
            'viewer_alpha'
        );

        self::assertSame(Response::HTTP_CREATED, $response->getStatusCode());
        self::assertNotNull(self::repository()->findByResource('media', $resourceId, 'en'));
    }

    public function testManagerWithoutSecurityCheckerKeepsWorking(): void
    {
        $resourceId = Resources::id('beta', 'without-checker');

        $manager = new PreviewLinkManager(
            self::repository(),
            self::service('sulu_activity.domain_event_collector'),
            self::service('sulu_preview.preview_object_provider_registry'),
            self::service('router')
        );

        $manager->generate('pages', $resourceId, 'en', []);

        self::assertNotNull(self::repository()->findByResource('pages', $resourceId, 'en'));
    }

    public function testShareWithMatchingWebspaceIsAllowed(): void
    {
        $resourceId = Resources::id('beta', 'share-allowed');

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '/share?resourceKey=pages&locale=en&webspaceKey=beta',
            'viewer_beta'
        );

        self::assertSame(Response::HTTP_CREATED, $response->getStatusCode());
        $stored = self::repository()->findByResource('pages', $resourceId, 'en');
        self::assertNotNull($stored);
        self::assertSame('beta', $stored->getOptions()['webspaceKey'] ?? null);
    }

    public function testViewerCanRotateAnExistingLink(): void
    {
        $resourceId = Resources::id('beta', 'rotate-allowed');
        $previewLink = $this->createLink('pages', $resourceId, 'en', ['webspaceKey' => 'beta']);

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '/rotate?resourceKey=pages&locale=en',
            'viewer_beta'
        );

        self::assertSame(Response::HTTP_CREATED, $response->getStatusCode());
        $stored = self::repository()->findByResource('pages', $resourceId, 'en');
        self::assertNotNull($stored);
        self::assertNotSame($previewLink->getToken(), $stored->getToken());
        self::assertNull(self::repository()->findByToken($previewLink->getToken()));
    }

    public function testUnknownLinkIsNotFound(): void
    {
        $resourceId = Resources::id('alpha', 'unknown');

        $response = $this->http(
            'GET',
            '/admin/api/preview-links/' . $resourceId . '?resourceKey=pages&locale=en',
            'admin'
        );

        self::assertSame(Response::HTTP_NOT_FOUND, $response->getStatusCode());
    }

    public function testUnknownActionIsRejected(): void
    {
        $resourceId = Resources::id('alpha', 'unknown-action');

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '?action=archive&resourceKey=pages&locale=en',
            'admin'
        );

        self::assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
    }

    public function testPublicTokenRoutesStayUnAuthenticated(): void
    {
        $resourceId = Resources::id('beta', 'public');
        $previewLink = $this->createLink('pages', $resourceId, 'en', ['webspaceKey' => 'beta']);
        $token = $previewLink->getToken();

        $response = $this->http('GET', '/admin/p/' . $token, 'attacker');
        self::assertSame(Response::HTTP_OK, $response->getStatusCode());

        $response = $this->http(
            'GET',
            '/admin/p/' . $token . '/render?locale=en&webspaceKey=beta',
            'attacker'
        );
        self::assertSame(Response::HTTP_OK, $response->getStatusCode());
        self::assertStringContainsString('rendered:' . $resourceId, (string) $response->getContent());
    }

    private function json(Response $response): array
    {
        $data = \json_decode((string) $response->getContent(), true);
        self::assertIsArray($data);

        return $data;
    }
}
