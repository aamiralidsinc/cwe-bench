<?php

namespace CweTests\Functional;

use CweTests\HiddenTestCase;

/**
 * Ordinary header decoding keeps behaving as it does today.
 */
class DecodingUseTest extends HiddenTestCase
{
    private function attachmentWithDisposition(string $disposition) : string
    {
        return $this->attachmentMessage("Content-Disposition: " . $disposition . "\r\n");
    }

    public function testEncodedWordSubjectDecodes() : void
    {
        $raw = "From: sender@example.test\r\n"
            . "Subject: =?UTF-8?B?" . \base64_encode('Résumé for the quarter') . "?=\r\n"
            . "Content-Type: text/plain\r\n"
            . "\r\n"
            . "Message body.\r\n";
        $this->assertSame('Résumé for the quarter', $this->parse($raw)->getSubject());
    }

    public function testFoldedHeadersUnfold() : void
    {
        $raw = "From: sender@example.test\r\n"
            . "Subject: Quarterly\r\n report\r\n"
            . "MIME-Version: 1.0\r\n"
            . "Content-Type: multipart/mixed; boundary=\"BOUNDARY\"\r\n"
            . "\r\n"
            . "--BOUNDARY\r\n"
            . "Content-Type: text/plain\r\n"
            . "Content-Disposition: attachment; filename=\"safe\r\n long-name.txt\"\r\n"
            . "\r\n"
            . "ATTACHMENT-BODY\r\n"
            . "--BOUNDARY--\r\n";
        $message = $this->parse($raw);
        $this->assertSame('Quarterly report', $message->getSubject());
        $part = $message->getAttachmentPart(0);
        $this->assertNotNull($part);
        $this->assertSame('safe long-name.txt', $part->getFilename());
    }

    public function testRfc2231FilenameDecodes() : void
    {
        $message = $this->parse($this->attachmentWithDisposition(
            "attachment; filename*=UTF-8''na%C3%AFve.txt"
        ));
        $part = $message->getAttachmentPart(0);
        $this->assertNotNull($part);
        $this->assertSame('naïve.txt', $part->getFilename());
    }

    public function testSplitParameterFilenameDecodes() : void
    {
        $message = $this->parse($this->attachmentWithDisposition(
            "attachment; filename*0*=UTF-8''na%C3%AFve; filename*1*=%20name.txt"
        ));
        $part = $message->getAttachmentPart(0);
        $this->assertNotNull($part);
        $this->assertSame('naïve name.txt', $part->getFilename());
    }

    public function testQuotedPairEscapesDecode() : void
    {
        $message = $this->parse($this->attachmentWithDisposition(
            "attachment; filename=\"say \\\"hi\\\".txt\""
        ));
        $part = $message->getAttachmentPart(0);
        $this->assertNotNull($part);
        $this->assertSame('say "hi".txt', $part->getFilename());
    }
}
