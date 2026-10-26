<?php

/**
 * Hidden security suite: FAQ records that are not publicly visible must not be disclosed by
 * any public read surface of the installation.
 */

declare(strict_types=1);

namespace phpMyFAQ\Verifier;

use FaqVisibilityFixture;
use phpMyFAQ\Controller\Api\FaqController;
use phpMyFAQ\Controller\Api\PdfController;
use phpMyFAQ\Controller\Api\SearchController;
use PHPUnit\Framework\Attributes\AllowMockObjectsWithoutExpectations;
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;

require_once __DIR__ . '/../harness/FaqVisibilityFixture.php';

#[AllowMockObjectsWithoutExpectations]
final class VisibilitySecurityTest extends TestCase
{
    private FaqVisibilityFixture $fixture;

    protected function setUp(): void
    {
        $this->fixture = FaqVisibilityFixture::boot();
        $this->fixture->reset();
    }

    private function assertNotDisclosed(JsonResponse $response, string $marker): void
    {
        self::assertStringNotContainsString(
            $marker,
            (string) $response->getContent(),
            'a FAQ that is not publicly visible was disclosed by a public read surface',
        );
    }

    private function faqRequest(array $attributes): Request
    {
        return new Request([], [], $attributes);
    }

    private function assertRecordIdAbsent(JsonResponse $response, int $recordId): void
    {
        $payload = json_decode((string) $response->getContent(), true);
        if (!is_array($payload)) {
            return;
        }

        if (isset($payload['id']) && (int) $payload['id'] === $recordId) {
            self::fail('a non-public FAQ identifier was disclosed');
        }

        foreach ($payload as $entry) {
            if (!is_array($entry)) {
                continue;
            }

            foreach (['id', 'record_id', 'faq_id'] as $key) {
                if (isset($entry[$key]) && (int) $entry[$key] === $recordId) {
                    self::fail('a non-public FAQ identifier was disclosed');
                }
            }
        }
    }


    public function testDetailRouteDoesNotDiscloseInactiveFaq(): void
    {
        $this->fixture->seed(2201, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2202, 'inactive', 'MARKINACTIVE');

        $controller = new FaqController();
        $response = $controller->getById($this->faqRequest(['categoryId' => '1', 'faqId' => '2202']));

        $this->assertNotDisclosed($response, 'MARKINACTIVE');
        $this->assertRecordIdAbsent($response, 2202);
    }

    public function testDetailRouteDoesNotDiscloseScheduledFaq(): void
    {
        $this->fixture->seed(2211, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2212, 'scheduled', 'MARKSCHEDULED');

        $controller = new FaqController();
        $response = $controller->getById($this->faqRequest(['categoryId' => '1', 'faqId' => '2212']));

        $this->assertNotDisclosed($response, 'MARKSCHEDULED');
        $this->assertRecordIdAbsent($response, 2212);
    }

    public function testDetailRouteDoesNotDiscloseExpiredFaq(): void
    {
        $this->fixture->seed(2221, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2222, 'expired', 'MARKEXPIRED');

        $controller = new FaqController();
        $response = $controller->getById($this->faqRequest(['categoryId' => '1', 'faqId' => '2222']));

        $this->assertNotDisclosed($response, 'MARKEXPIRED');
        $this->assertRecordIdAbsent($response, 2222);
    }

    public function testTagRouteDoesNotDiscloseNonPublicFaqs(): void
    {
        $this->fixture->seed(2301, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2302, 'inactive', 'MARKINACTIVE');
        $this->fixture->seed(2303, 'scheduled', 'MARKSCHEDULED');
        $this->fixture->seed(2304, 'expired', 'MARKEXPIRED');

        $controller = new FaqController();
        $response = $controller->getByTagId($this->faqRequest(['tagId' => (string) FaqVisibilityFixture::TAG]));

        $this->assertNotDisclosed($response, 'MARKINACTIVE');
        $this->assertNotDisclosed($response, 'MARKSCHEDULED');
        $this->assertNotDisclosed($response, 'MARKEXPIRED');
        $this->assertRecordIdAbsent($response, 2302);
        $this->assertRecordIdAbsent($response, 2303);
        $this->assertRecordIdAbsent($response, 2304);
    }

    public function testListRouteDoesNotDiscloseNonPublicFaqs(): void
    {
        $this->fixture->seed(2401, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2402, 'inactive', 'MARKINACTIVE');
        $this->fixture->seed(2403, 'scheduled', 'MARKSCHEDULED');
        $this->fixture->seed(2404, 'expired', 'MARKEXPIRED');

        $controller = new FaqController();
        $response = $controller->list();

        $this->assertNotDisclosed($response, 'MARKINACTIVE');
        $this->assertNotDisclosed($response, 'MARKSCHEDULED');
        $this->assertNotDisclosed($response, 'MARKEXPIRED');
        $this->assertRecordIdAbsent($response, 2402);
        $this->assertRecordIdAbsent($response, 2403);
        $this->assertRecordIdAbsent($response, 2404);
    }

    public function testSearchDoesNotDiscloseScheduledFaq(): void
    {
        $this->fixture->seed(2501, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2502, 'scheduled', 'MARKSCHEDULED');

        $controller = new SearchController();
        $response = $controller->search(new Request(['q' => 'MARKSCHEDULED']));

        $this->assertNotDisclosed($response, 'MARKSCHEDULED');
        $this->assertRecordIdAbsent($response, 2502);
    }

    public function testSearchDoesNotDiscloseExpiredFaq(): void
    {
        $this->fixture->seed(2511, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2512, 'expired', 'MARKEXPIRED');

        $controller = new SearchController();
        $response = $controller->search(new Request(['q' => 'MARKEXPIRED']));

        $this->assertNotDisclosed($response, 'MARKEXPIRED');
        $this->assertRecordIdAbsent($response, 2512);
    }

    public function testPdfRouteDoesNotLinkToInactiveFaq(): void
    {
        $this->fixture->seed(2601, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2602, 'inactive', 'MARKINACTIVE');

        $controller = new PdfController();
        $response = $controller->getById($this->faqRequest(['categoryId' => '1', 'faqId' => '2602']));

        self::assertStringNotContainsString('id=2602', (string) $response->getContent());
    }

    public function testPdfRouteDoesNotLinkToScheduledFaq(): void
    {
        $this->fixture->seed(2611, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2612, 'scheduled', 'MARKSCHEDULED');

        $controller = new PdfController();
        $response = $controller->getById($this->faqRequest(['categoryId' => '1', 'faqId' => '2612']));

        self::assertStringNotContainsString('id=2612', (string) $response->getContent());
    }

    public function testFeedDoesNotDiscloseScheduledFaq(): void
    {
        $this->fixture->seed(2701, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2702, 'scheduled', 'MARKSCHEDULED');

        $controller = new FaqController();
        $response = $controller->getFeed();

        $this->assertNotDisclosed($response, 'MARKSCHEDULED');
        $this->assertRecordIdAbsent($response, 2702);
    }

    public function testFeedDoesNotDiscloseExpiredFaq(): void
    {
        $this->fixture->seed(2711, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2712, 'expired', 'MARKEXPIRED');

        $controller = new FaqController();
        $response = $controller->getFeed();

        $this->assertNotDisclosed($response, 'MARKEXPIRED');
        $this->assertRecordIdAbsent($response, 2712);
    }

    public function testPreviewDoesNotDiscloseInactiveFaq(): void
    {
        $this->fixture->seed(2801, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2802, 'inactive', 'MARKINACTIVE');

        $controller = new FaqController();
        $response = $controller->preview($this->faqRequest(['faqId' => '2802']));

        $this->assertNotDisclosed($response, 'MARKINACTIVE');
        $this->assertRecordIdAbsent($response, 2802);
    }

    public function testPreviewDoesNotDiscloseScheduledFaq(): void
    {
        $this->fixture->seed(2811, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2812, 'scheduled', 'MARKSCHEDULED');

        $controller = new FaqController();
        $response = $controller->preview($this->faqRequest(['faqId' => '2812']));

        $this->assertNotDisclosed($response, 'MARKSCHEDULED');
        $this->assertRecordIdAbsent($response, 2812);
    }

    public function testPreviewDoesNotDiscloseExpiredFaq(): void
    {
        $this->fixture->seed(2821, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(2822, 'expired', 'MARKEXPIRED');

        $controller = new FaqController();
        $response = $controller->preview($this->faqRequest(['faqId' => '2822']));

        $this->assertNotDisclosed($response, 'MARKEXPIRED');
        $this->assertRecordIdAbsent($response, 2822);
    }
}
