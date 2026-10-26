<?php

namespace CweTests\Security;

use CweTests\HiddenTestCase;

/**
 * Values the application supplies when it embeds an inline image must not add
 * header lines to the message the library writes.
 */
class InlineImageTest extends HiddenTestCase
{
    private function htmlMessage() : string
    {
        return $this->baseMessage('text/html; charset=UTF-8');
    }

    public function testInlineImageNameDoesNotAddHeaderLine() : void
    {
        $message = $this->parse($this->htmlMessage());
        try {
            $message->addInlineImage(
                'IMAGE-BODY',
                'image/png',
                "logo.png\r\nX-Image: hidden@example.test",
                'logo@example.test'
            );
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoInjectedLine($output, 'X-Image');
    }

    public function testInlineImageContentIdDoesNotAddHeaderLine() : void
    {
        $message = $this->parse($this->htmlMessage());
        try {
            $message->addInlineImage(
                'IMAGE-BODY',
                'image/png',
                'logo.png',
                "logo@example.test\r\nX-Image: hidden@example.test"
            );
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoInjectedLine($output, 'X-Image');
    }
}
