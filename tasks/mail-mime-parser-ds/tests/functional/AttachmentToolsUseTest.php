<?php

namespace CweTests\Functional;

use CweTests\HiddenTestCase;

/**
 * Ordinary use of the attachment-name, inline-image and non-mime attachment
 * features keeps behaving as it does today.
 */
class AttachmentToolsUseTest extends HiddenTestCase
{
    public function testRenameAttachmentKeepsTheNewName() : void
    {
        $message = $this->parse($this->baseMessage());
        $message->addAttachmentPart('ATTACHMENT-BODY', 'application/pdf', 'report.pdf');
        $message->renameAttachment(0, 'new name.pdf');

        $part = $message->getAttachmentPart(0);
        $this->assertNotNull($part);
        $this->assertSame('new name.pdf', $part->getFilename());

        $reparsed = $this->parse($this->messageText($message));
        $this->assertSame('new name.pdf', $reparsed->getAttachmentPart(0)->getFilename());
        $this->assertStringContainsString(";\r\n\tfilename=\"new name.pdf\"", $this->messageText($message));
    }

    public function testInlineImageKeepsItsNameAndContentId() : void
    {
        $message = $this->parse($this->baseMessage('text/html; charset=UTF-8'));
        $message->addInlineImage('IMAGE-BODY', 'image/png', 'logo.png', 'logo@example.test');
        $output = $this->messageText($message);

        $this->assertStringContainsString('name="logo.png"', $output);
        $this->assertStringContainsString('filename="logo.png"', $output);
        $this->assertStringContainsString('Content-ID: <logo@example.test>', $output);
    }

    public function testUUEncodedAttachmentKeepsItsBeginLineName() : void
    {
        $message = $this->parse(
            "From: sender@example.test\r\n"
            . "Subject: plain message\r\n"
            . "\r\n"
            . "Message body.\r\n"
        );
        $message->addAttachmentPart('ATTACHMENT-BODY', 'application/octet-stream', 'notes.txt');
        $this->assertStringContainsString("begin 666 notes.txt\r\n", $this->messageText($message));

        $message->renameAttachment(0, 'other.txt');
        $output = $this->messageText($message);
        $this->assertStringContainsString("begin 666 other.txt\r\n", $output);
        $this->assertSame('other.txt', $message->getAllAttachmentParts()[0]->getFilename());
    }
}
