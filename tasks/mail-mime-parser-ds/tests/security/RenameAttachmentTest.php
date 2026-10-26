<?php

namespace CweTests\Security;

use CweTests\HiddenTestCase;

/**
 * A new name the application supplies for an existing attachment must not add
 * a header line to the message the library writes.
 */
class RenameAttachmentTest extends HiddenTestCase
{
    public function testRenamedAttachmentNameDoesNotAddHeaderLine() : void
    {
        $message = $this->parse($this->baseMessage());
        try {
            $message->addAttachmentPart(
                'ATTACHMENT-BODY',
                'application/pdf',
                'report.pdf',
                'attachment',
                'base64'
            );
            $message->renameAttachment(0, "renamed.pdf\r\nX-Rename: hidden@example.test");
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoInjectedLine($output, 'X-Rename');
        $this->assertNoLineBreak($message->getAttachmentPart(0)->getFilename());
    }
}
