<?php

namespace CweTests\Security;

use CweTests\HiddenTestCase;

/**
 * Values the application supplies for the parameters of a signed message must
 * not add header lines to the message the library writes.
 */
class SigningParametersTest extends HiddenTestCase
{
    public function testSigningParametersDoNotAddHeaderLines() : void
    {
        $message = $this->parse($this->baseMessage());
        try {
            $message->setAsMultipartSigned(
                "pgp-sha256\r\nX-Micalg: hidden@example.test",
                "application/pgp-signature\r\nX-Signing: second@example.test"
            );
            $output = $this->messageText($message);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);
            return;
        }
        $this->assertStringContainsString('multipart/signed', $output);
        $this->assertNoInjectedLine($output, 'X-Micalg');
        $this->assertNoInjectedLine($output, 'X-Signing');
    }
}
