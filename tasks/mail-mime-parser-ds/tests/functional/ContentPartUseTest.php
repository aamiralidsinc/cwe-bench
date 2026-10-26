<?php

namespace CweTests\Functional;

use CweTests\HiddenTestCase;

/**
 * Ordinary content-part use keeps behaving as it does today.
 */
class ContentPartUseTest extends HiddenTestCase
{
    public function testCharsetOnNewContentPartIsKept() : void
    {
        $message = $this->parse(
            "From: sender@example.test\r\n"
            . "MIME-Version: 1.0\r\n"
            . "Content-Type: multipart/mixed; boundary=\"BOUNDARY\"\r\n"
            . "\r\n"
            . "--BOUNDARY--\r\n"
        );
        $message->setTextPart('Message body.', 'UTF-8');
        $output = $this->messageText($message);

        $this->assertStringContainsString('charset="UTF-8"', $output);
        $part = $this->parse($output)->getTextPart();
        $this->assertNotNull($part);
        $this->assertSame('UTF-8', $part->getCharset());
        $this->assertStringContainsString('Message body.', (string) $part->getContent());
    }

    public function testCharsetOnExistingContentPartIsKept() : void
    {
        $message = $this->parse($this->baseMessage());
        $message->setTextPart('Message body.', 'ISO-8859-1');
        $output = $this->messageText($message);

        $this->assertStringContainsString('charset="ISO-8859-1"', $output);
        $part = $this->parse($output)->getTextPart();
        $this->assertNotNull($part);
        $this->assertSame('ISO-8859-1', $part->getCharset());
    }
}
