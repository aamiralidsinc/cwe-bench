<?php

namespace CweTests\Security;

use CweTests\HiddenTestCase;

/**
 * Values the library decodes out of a message it reads must not carry a line
 * break back to the application, and must not become header lines when the
 * library writes them into a message it composes.
 */
class DecodedHeaderValueTest extends HiddenTestCase
{
    private function filenameOfMessage(string $raw) : array
    {
        $message = $this->parse($raw);
        $part = $message->getAttachmentPart(0);
        return [$message, $part, ($part !== null) ? $part->getFilename() : null];
    }

    public function testParameterFilenameHasNoLineBreak() : void
    {
        $raw = $this->attachmentMessage(
            "Content-Disposition: attachment; filename*=UTF-8''report.txt%0D%0AX-Param:%20hidden@example.test\r\n"
        );
        try {
            list(, $part, $name) = $this->filenameOfMessage($raw);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNotNull($part);
        $this->assertNoLineBreak($name);
    }

    public function testSplitParameterFilenameHasNoLineBreak() : void
    {
        $raw = $this->attachmentMessage(
            "Content-Disposition: attachment; filename*0*=UTF-8''report.txt%0D%0A; filename*1*=X-Split:%20hidden@example.test\r\n"
        );
        try {
            list(, $part, $name) = $this->filenameOfMessage($raw);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNotNull($part);
        $this->assertNoLineBreak($name);
    }

    public function testEncodedWordFilenameHasNoLineBreak() : void
    {
        $payload = "report.txt\r\nX-Word: hidden@example.test";
        $raw = "From: sender@example.test\r\n"
            . "To: recipient@example.test\r\n"
            . "MIME-Version: 1.0\r\n"
            . "Content-Type: multipart/mixed; boundary=\"BOUNDARY\"\r\n"
            . "\r\n"
            . "--BOUNDARY\r\n"
            . "Content-Type: text/plain; name=\"=?UTF-8?B?" . \base64_encode($payload) . "?=\"\r\n"
            . "Content-Disposition: attachment\r\n"
            . "\r\n"
            . "ATTACHMENT-BODY\r\n"
            . "--BOUNDARY--\r\n";
        try {
            list(, $part, $name) = $this->filenameOfMessage($raw);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNotNull($part);
        $this->assertNoLineBreak($name);
    }

    public function testEncodedWordSubjectHasNoLineBreak() : void
    {
        $payload = "Quarterly report\r\nX-Subject: hidden@example.test";
        $raw = "From: sender@example.test\r\n"
            . "Subject: =?UTF-8?B?" . \base64_encode($payload) . "?=\r\n"
            . "Content-Type: text/plain\r\n"
            . "\r\n"
            . "Message body.\r\n";
        try {
            $subject = $this->parse($raw)->getSubject();
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoLineBreak($subject);
    }

    public function testProtocolCopiedWhenSigningIsNotWrittenAsHeader() : void
    {
        $raw = "From: sender@example.test\r\n"
            . "MIME-Version: 1.0\r\n"
            . "Content-Type: multipart/signed; boundary=\"SIGN\"; "
            . "protocol*0*=UTF-8''application/pgp-signature%0D%0AX-Protocol:%20hidden@example.test; protocol*1*=''\r\n"
            . "\r\n"
            . "--SIGN\r\n"
            . "Content-Type: text/plain\r\n"
            . "\r\n"
            . "Message body.\r\n"
            . "--SIGN--\r\n";
        try {
            $message = $this->parse($raw);
            $message->setSignature('SIGNATURE-BODY');
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoInjectedLine($output, 'X-Protocol');
    }
}
