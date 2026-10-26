<?php

namespace CweTests;

use PHPUnit\Framework\TestCase;
use ZBateson\MailMimeParser\MailMimeParser;

/**
 * Shared helpers for the hidden suites.
 *
 * Everything here is computed from the inputs the test itself supplies; no
 * expected value is read back out of the library under test.
 */
abstract class HiddenTestCase extends TestCase
{
    protected function parser() : MailMimeParser
    {
        return new MailMimeParser();
    }

    protected function parse(string $raw)
    {
        return $this->parser()->parse($raw, false);
    }

    protected function messageText($message) : string
    {
        return $message->getStream()->getContents();
    }

    /**
     * Fails when the composed text contains a line that begins with the given
     * header name: the application supplied one value, not a header line.
     */
    protected function assertNoInjectedLine(string $output, string $header = 'Bcc') : void
    {
        $this->assertDoesNotMatchRegularExpression(
            '/^[ \t]*' . \preg_quote($header, '/') . '[ \t]*:/mi',
            $output,
            'the composed message contains a header line the application never supplied'
        );
    }

    protected function assertNoLineBreak(?string $value) : void
    {
        if ($value === null) {
            return;
        }
        $this->assertDoesNotMatchRegularExpression('/[\r\n]/', $value, 'the value carries a line break');
    }

    protected function baseMessage(string $contentType = 'text/plain; charset=UTF-8') : string
    {
        return "From: sender@example.test\r\n"
            . "To: recipient@example.test\r\n"
            . "Subject: quarterly report\r\n"
            . "MIME-Version: 1.0\r\n"
            . "Content-Type: " . $contentType . "\r\n"
            . "\r\n"
            . "Message body.\r\n";
    }

    /**
     * A multipart message with a single attachment part.  $headers are placed
     * after the part's Content-Type header.
     */
    protected function attachmentMessage(string $partHeaders, string $partContentType = 'text/plain') : string
    {
        return "From: sender@example.test\r\n"
            . "To: recipient@example.test\r\n"
            . "Subject: quarterly report\r\n"
            . "MIME-Version: 1.0\r\n"
            . "Content-Type: multipart/mixed; boundary=\"BOUNDARY\"\r\n"
            . "\r\n"
            . "--BOUNDARY\r\n"
            . "Content-Type: " . $partContentType . "\r\n"
            . $partHeaders
            . "\r\n"
            . "ATTACHMENT-BODY\r\n"
            . "--BOUNDARY--\r\n";
    }
}
