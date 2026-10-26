<?php

namespace CweTests\Security;

use CweTests\HiddenTestCase;

/**
 * A name the application supplies for an attached file must not add a header
 * line to the message the library writes.
 */
class AttachmentNameTest extends HiddenTestCase
{
    public function testAttachmentNameWithHeaderLineIsNotWritten() : void
    {
        $message = $this->parse($this->baseMessage());
        try {
            $message->addAttachmentPart(
                'ATTACHMENT-BODY',
                'application/octet-stream',
                "report.txt\r\nX-Attachment: hidden@example.test",
                'attachment',
                'base64'
            );
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }

        $this->assertCount(1, $message->getAllAttachmentParts());
        $this->assertNoInjectedLine($output, 'X-Attachment');
        $this->assertNoLineBreak($message->getAttachmentPart(0)->getFilename());
    }
}
