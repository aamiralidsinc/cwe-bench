<?php

namespace Sulu\Task\Tests\Security;

use Sulu\Task\Harness\PreviewTestCase;
use Sulu\Task\Harness\Resources;

class PreviewLinkAuthorizationSecurityTest extends PreviewTestCase
{
    public function testAdminGenerateDeniedForUserWithoutViewPermission(): void
    {
        $resourceId = Resources::id('beta', 'generate-denied');

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '?action=generate&resourceKey=pages&locale=en',
            'attacker'
        );

        self::assertClientError($response);
        self::assertNull(self::repository()->findByResource('pages', $resourceId, 'en'));
    }

    public function testAdminGenerateDeniedForViewerOfAnotherWebspace(): void
    {
        $resourceId = Resources::id('beta', 'generate-other-webspace');

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '?action=generate&resourceKey=pages&locale=en',
            'viewer_alpha'
        );

        self::assertClientError($response);
        self::assertNull(self::repository()->findByResource('pages', $resourceId, 'en'));
    }

    public function testAdminRevokeDeniedForUserWithoutViewPermission(): void
    {
        $resourceId = Resources::id('beta', 'revoke-denied');
        $previewLink = $this->createLink('pages', $resourceId, 'en', ['webspaceKey' => 'beta']);

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '?action=revoke&resourceKey=pages&locale=en',
            'attacker'
        );

        self::assertClientError($response);
        $stored = self::repository()->findByResource('pages', $resourceId, 'en');
        self::assertNotNull($stored);
        self::assertSame($previewLink->getToken(), $stored->getToken());
    }

    public function testServiceGenerateDeniedForUserWithoutViewPermission(): void
    {
        $resourceId = Resources::id('beta', 'service-generate-denied');
        $this->actAs('attacker');

        $manager = self::service('sulu_preview.preview_link_manager');

        try {
            $manager->generate('pages', $resourceId, 'en', []);
        } catch (\Throwable $exception) {
            // a refusal is the expected outcome; the side effect is checked below
        }

        self::assertNull(self::repository()->findByResource('pages', $resourceId, 'en'));
    }

    public function testServiceRevokeDeniedForUserWithoutViewPermission(): void
    {
        $resourceId = Resources::id('beta', 'service-revoke-denied');
        $previewLink = $this->createLink('pages', $resourceId, 'en', ['webspaceKey' => 'beta']);
        $this->actAs('attacker');

        $manager = self::service('sulu_preview.preview_link_manager');

        try {
            $manager->revoke('pages', $resourceId, 'en');
        } catch (\Throwable $exception) {
            // a refusal is the expected outcome; the side effect is checked below
        }

        $stored = self::repository()->findByResource('pages', $resourceId, 'en');
        self::assertNotNull($stored);
        self::assertSame($previewLink->getToken(), $stored->getToken());
    }

    public function testReadDeniedForUserWithoutViewPermission(): void
    {
        $resourceId = Resources::id('beta', 'read-denied');
        $previewLink = $this->createLink('pages', $resourceId, 'en', ['webspaceKey' => 'beta']);

        $response = $this->http(
            'GET',
            '/admin/api/preview-links/' . $resourceId . '?resourceKey=pages&locale=en',
            'attacker'
        );

        self::assertClientError($response);
        self::assertStringNotContainsString($previewLink->getToken(), (string) $response->getContent());
    }

    public function testReadDeniedForViewerOfAnotherWebspace(): void
    {
        $resourceId = Resources::id('beta', 'read-other-webspace');
        $previewLink = $this->createLink('pages', $resourceId, 'en', ['webspaceKey' => 'beta']);

        $response = $this->http(
            'GET',
            '/admin/api/preview-links/' . $resourceId . '?resourceKey=pages&locale=en',
            'viewer_alpha'
        );

        self::assertClientError($response);
        self::assertStringNotContainsString($previewLink->getToken(), (string) $response->getContent());
    }

    public function testShareDeniedWhenNamedWebspaceDiffersFromContent(): void
    {
        $resourceId = Resources::id('beta', 'share-other-webspace');

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '/share?resourceKey=pages&locale=en&webspaceKey=alpha',
            'viewer_alpha'
        );

        self::assertClientError($response);
        self::assertNull(self::repository()->findByResource('pages', $resourceId, 'en'));
    }

    public function testRotateDeniedForUserWithoutViewPermission(): void
    {
        $resourceId = Resources::id('beta', 'rotate-denied');
        $previewLink = $this->createLink('pages', $resourceId, 'en', ['webspaceKey' => 'beta']);

        $response = $this->http(
            'POST',
            '/admin/api/preview-links/' . $resourceId . '/rotate?resourceKey=pages&locale=en',
            'attacker'
        );

        self::assertClientError($response);
        $stored = self::repository()->findByResource('pages', $resourceId, 'en');
        self::assertNotNull($stored);
        self::assertSame($previewLink->getToken(), $stored->getToken());
    }
}
