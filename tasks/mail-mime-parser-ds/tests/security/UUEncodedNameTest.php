<?php

namespace CweTests\Security;

use CweTests\HiddenTestCase;

/**
 * A name set on a non-mime message's attachment is written next to the encoded
 * content; it must not add a line to the message the library writes.
 */
class UUEncodedNameTest extends HiddenTestCase
{
    public function testUUEncodedFilenameDoesNotAddLine() : void
    {
        $message = $this->parse(
            "From: sender@example.test\r\n"
            . "Subject: plain message\r\n"
            . "\r\n"
            . "Message body.\r\n"
        );
        try {
            $message->addAttachmentPart(
                'ATTACHMENT-BODY',
                'application/octet-stream',
                'report.bin',
                'attachment',
                'base64'
            );
            $parts = $message->getAllAttachmentParts();
            $this->assertCount(1, $parts);
            $parts[0]->setFilename("report.bin\r\nX-Begin: hidden@example.test");
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoInjectedLine($output, 'X-Begin');
        $this->assertNoLineBreak($parts[0]->getFilename());
    }
}
