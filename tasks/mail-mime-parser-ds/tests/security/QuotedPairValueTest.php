<?php

namespace CweTests\Security;

use CweTests\HiddenTestCase;

/**
 * A quoted-pair continuation inside a header value must not become a line
 * break in the value the library returns.
 */
class QuotedPairValueTest extends HiddenTestCase
{
    private function nameFrom(string $disposition) : ?string
    {
        $raw = $this->attachmentMessage("Content-Disposition: " . $disposition . "\r\n");
        $part = $this->parse($raw)->getAttachmentPart(0);
        $this->assertNotNull($part);
        return $part->getFilename();
    }

    public function testQuotedContinuationHasNoLineBreak() : void
    {
        try {
            $name = $this->nameFrom("attachment; filename=\"report.txt\\\r\n X-Quoted: hidden@example.test\"");
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoLineBreak($name);
    }

    public function testUnquotedContinuationHasNoLineBreak() : void
    {
        try {
            $name = $this->nameFrom("attachment; filename=report.txt\\\r\n X-Quoted: hidden@example.test");
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertNoLineBreak($name);
    }
}
