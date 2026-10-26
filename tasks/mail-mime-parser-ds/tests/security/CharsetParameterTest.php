<?php

namespace CweTests\Security;

use CweTests\HiddenTestCase;

/**
 * A charset value the application supplies must not add a header line to the
 * message the library writes, whether the content part already exists or is
 * created for the call.
 */
class CharsetParameterTest extends HiddenTestCase
{
    public function testCharsetOnNewContentPartDoesNotAddHeaderLine() : void
    {
        $message = $this->parse(
            "From: sender@example.test\r\n"
            . "MIME-Version: 1.0\r\n"
            . "Content-Type: multipart/mixed; boundary=\"BOUNDARY\"\r\n"
            . "\r\n"
            . "--BOUNDARY--\r\n"
        );
        try {
            $message->setTextPart('Message body.', "UTF-8\r\nX-Charset: hidden@example.test");
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoInjectedLine($output, 'X-Charset');
    }

    public function testCharsetOnExistingContentPartDoesNotAddHeaderLine() : void
    {
        $message = $this->parse($this->baseMessage());
        try {
            $message->setTextPart('Message body.', "UTF-8\r\nX-Charset: hidden@example.test");
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoInjectedLine($output, 'X-Charset');
    }
}
