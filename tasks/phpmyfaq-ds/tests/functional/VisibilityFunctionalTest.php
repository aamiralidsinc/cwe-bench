<?php

/**
 * Hidden functional suite: publicly visible FAQ records keep working exactly as today, and the
 * privileged administrative/editing behaviour keeps its access.
 */

declare(strict_types=1);

namespace phpMyFAQ\Verifier;

use FaqVisibilityFixture;
use phpMyFAQ\Category;
use phpMyFAQ\Controller\Api\FaqController;
use phpMyFAQ\Controller\Api\PdfController;
use phpMyFAQ\Controller\Api\SearchController;
use phpMyFAQ\Export\Json as JsonExport;
use phpMyFAQ\Faq;
use PHPUnit\Framework\Attributes\AllowMockObjectsWithoutExpectations;
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;

require_once __DIR__ . '/../harness/FaqVisibilityFixture.php';

#[AllowMockObjectsWithoutExpectations]
final class VisibilityFunctionalTest extends TestCase
{
    private FaqVisibilityFixture $fixture;

    protected function setUp(): void
    {
        $this->fixture = FaqVisibilityFixture::boot();
        $this->fixture->reset();
    }

    private function faqRequest(array $attributes): Request
    {
        return new Request([], [], $attributes);
    }

    private function assertDisclosed(JsonResponse $response, string $marker): void
    {
        self::assertStringContainsString(
            $marker,
            (string) $response->getContent(),
            'a publicly visible FAQ stopped being returned',
        );
    }

    public function testDetailRouteReturnsVisibleFaq(): void
    {
        $this->fixture->seed(3101, 'visible', 'MARKVISIBLE');

        $controller = new FaqController();
        $response = $controller->getById($this->faqRequest(['categoryId' => '1', 'faqId' => '3101']));

        self::assertSame(200, $response->getStatusCode());
        $this->assertDisclosed($response, 'MARKVISIBLE');
        $payload = json_decode((string) $response->getContent(), true, 512, JSON_THROW_ON_ERROR);
        self::assertSame(3101, $payload['id']);
        self::assertSame('yes', $payload['active']);
    }

    public function testDetailRouteReturnsFaqWithOpenWindow(): void
    {
        $this->fixture->seed(3111, 'windowed', 'MARKWINDOWED');

        $controller = new FaqController();
        $response = $controller->getById($this->faqRequest(['categoryId' => '1', 'faqId' => '3111']));

        self::assertSame(200, $response->getStatusCode());
        $this->assertDisclosed($response, 'MARKWINDOWED');
    }

    public function testListRouteReturnsVisibleFaqs(): void
    {
        $this->fixture->seed(3201, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(3202, 'windowed', 'MARKWINDOWED');

        $controller = new FaqController();
        $response = $controller->list();

        self::assertSame(200, $response->getStatusCode());
        $this->assertDisclosed($response, 'MARKVISIBLE');
        $this->assertDisclosed($response, 'MARKWINDOWED');
    }

    public function testTagRouteReturnsVisibleFaq(): void
    {
        $this->fixture->seed(3301, 'visible', 'MARKVISIBLE');

        $controller = new FaqController();
        $response = $controller->getByTagId($this->faqRequest(['tagId' => (string) FaqVisibilityFixture::TAG]));

        self::assertSame(200, $response->getStatusCode());
        $this->assertDisclosed($response, 'MARKVISIBLE');
    }

    public function testSearchFindsVisibleFaq(): void
    {
        $this->fixture->seed(3401, 'visible', 'MARKVISIBLE');

        $controller = new SearchController();
        $response = $controller->search(new Request(['q' => 'MARKVISIBLE']));

        self::assertSame(200, $response->getStatusCode());
        $this->assertDisclosed($response, 'MARKVISIBLE');
    }

    public function testPdfRouteReturnsLinkForVisibleFaq(): void
    {
        $this->fixture->seed(3501, 'visible', 'MARKVISIBLE');

        $controller = new PdfController();
        $response = $controller->getById($this->faqRequest(['categoryId' => '1', 'faqId' => '3501']));

        self::assertSame(200, $response->getStatusCode());
        self::assertStringContainsString('id=3501', (string) $response->getContent());
    }

    public function testFeedReturnsVisibleFaqs(): void
    {
        $this->fixture->seed(3601, 'visible', 'MARKVISIBLE');

        $controller = new FaqController();
        $response = $controller->getFeed();

        self::assertSame(200, $response->getStatusCode());
        $this->assertDisclosed($response, 'MARKVISIBLE');
    }

    public function testPreviewReturnsVisibleFaq(): void
    {
        $this->fixture->seed(3701, 'visible', 'MARKVISIBLE');

        $controller = new FaqController();
        $response = $controller->preview($this->faqRequest(['faqId' => '3701']));

        self::assertSame(200, $response->getStatusCode());
        $this->assertDisclosed($response, 'MARKVISIBLE');
    }

    public function testAdminReaderStillReturnsInactiveFaq(): void
    {
        $this->fixture->seed(3801, 'inactive', 'MARKINACTIVE');

        $faq = new Faq($this->fixture->configuration);
        $faq->setUser(-1)->setGroups([-1]);
        $faq->getFaq(3801, null, true);

        self::assertSame(3801, (int) $faq->faqRecord['id']);
        self::assertStringContainsString('MARKINACTIVE', (string) $faq->faqRecord['title']);
        self::assertStringContainsString('MARKINACTIVE', (string) $faq->faqRecord['content']);
    }

    public function testAdminReaderStillReturnsScheduledFaq(): void
    {
        $this->fixture->seed(3811, 'scheduled', 'MARKSCHEDULED');

        $faq = new Faq($this->fixture->configuration);
        $faq->setUser(-1)->setGroups([-1]);
        $faq->getFaq(3811, null, true);

        self::assertSame(3811, (int) $faq->faqRecord['id']);
        self::assertStringContainsString('MARKSCHEDULED', (string) $faq->faqRecord['content']);
    }

    public function testAdminJsonExportStillIncludesScheduledFaq(): void
    {
        $this->fixture->seed(3901, 'visible', 'MARKVISIBLE');
        $this->fixture->seed(3902, 'scheduled', 'MARKSCHEDULED');

        $faq = new Faq($this->fixture->configuration);
        $faq->setUser(-1)->setGroups([-1]);
        $category = new Category($this->fixture->configuration);

        $export = new JsonExport($faq, $category, $this->fixture->configuration);
        $output = $export->generate(0, true, 'en');

        self::assertStringContainsString('MARKVISIBLE', $output);
        self::assertStringContainsString('MARKSCHEDULED', $output);
    }
}
