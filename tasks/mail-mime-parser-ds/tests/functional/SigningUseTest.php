<?php

namespace CweTests\Functional;

use CweTests\HiddenTestCase;

/**
 * Ordinary signing use keeps behaving as it does today.
 */
class SigningUseTest extends HiddenTestCase
{
    public function testSignedMessageKeepsItsParameters() : void
    {
        $message = $this->parse($this->baseMessage());
        $message->setAsMultipartSigned('pgp-sha256', 'application/pgp-signature');
        $message->setSignature('SIGNATURE-BODY');
        $output = $this->messageText($message);

        $this->assertStringContainsString('micalg="pgp-sha256"', $output);
        $this->assertStringContainsString('protocol="application/pgp-signature"', $output);

        $reparsed = $this->parse($output);
        $signature = $reparsed->getSignaturePart();
        $this->assertNotNull($signature);
        $this->assertSame('application/pgp-signature', $signature->getContentType());
    }
}
