<?php

namespace CweTests\Functional;

use CweTests\HiddenTestCase;

/**
 * Ordinary attachment use keeps behaving as it does today.
 */
class AttachmentUseTest extends HiddenTestCase
{
    public function testAttachRegularFileRoundTrips() : void
    {
        $message = $this->parse($this->baseMessage());
        $message->addAttachmentPart('ATTACHMENT-BODY', 'application/pdf', 'report.pdf');
        $output = $this->messageText($message);

        $reparsed = $this->parse($output);
        $this->assertSame(1, $reparsed->getAttachmentCount());
        $part = $reparsed->getAttachmentPart(0);
        $this->assertNotNull($part);
        $this->assertSame('report.pdf', $part->getFilename());
        $this->assertSame('application/pdf', $part->getContentType());
        $this->assertSame('ATTACHMENT-BODY', $part->getContent());
    }

    public function testNonAsciiNameIsTransliterated() : void
    {
        $message = $this->parse($this->baseMessage());
        $message->addAttachmentPart('ATTACHMENT-BODY', 'application/pdf', 'résumé.pdf');
        $output = $this->messageText($message);

        $part = $this->parse($output)->getAttachmentPart(0);
        $this->assertNotNull($part);
        $this->assertSame('resume.pdf', $part->getFilename());
    }

    public function testComposedHeadersKeepTheirFolding() : void
    {
        $message = $this->parse($this->baseMessage());
        $message->addAttachmentPart('ATTACHMENT-BODY', 'application/pdf', 'report.pdf');
        $output = $this->messageText($message);

        $this->assertStringContainsString(";\r\n\tboundary=\"", $output);
        $this->assertStringContainsString(";\r\n\tname=\"", $output);
        $this->assertStringContainsString(";\r\n\tfilename=\"", $output);
    }
}
