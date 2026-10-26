<?php

namespace CraftTask\Tests\Security;

use CraftTask\Harness\CraftTestCase;

/**
 * The session return destination: the value is stored by the product and handed back later as
 * the address the browser is sent to.
 */
class SessionReturnDestinationTest extends CraftTestCase
{
    private function store(string $payload): array
    {
        $app = $this->boot();
        $user = $app->getUser();
        $user->setReturnUrl($payload);
        $stored = $app->getSession()->get($user->returnUrlParam);
        return [(string)$stored, $user->getReturnUrl()];
    }

    public function testPlainScriptSchemeNeverSurvives(): void
    {
        [$stored, $returned] = $this->store('javascript:alert(document.domain)');
        self::assertSafeDestination($stored, 'stored return destination');
        self::assertSafeDestination($returned, 'returned destination');
    }

    public function testScriptSchemeAssembledByTemplateTagRemovalNeverSurvives(): void
    {
        [$stored, $returned] = $this->store('java{script:alert(document.domain)}');
        self::assertSafeDestination($stored, 'stored return destination');
        self::assertSafeDestination($returned, 'returned destination');
    }

    public function testScriptSchemeAssembledByMarkupRemovalNeverSurvives(): void
    {
        [$stored, $returned] = $this->store('java<script></script>script:alert(document.domain)');
        self::assertSafeDestination($stored, 'stored return destination');
        self::assertSafeDestination($returned, 'returned destination');
    }

    public function testMarkupIsNeverStored(): void
    {
        [$stored, $returned] = $this->store('<?php system("id"); ?>');
        self::assertSafeDestination($stored, 'stored return destination');
        self::assertSafeDestination($returned, 'returned destination');
    }

    public function testDataUrlNeverSurvives(): void
    {
        [$stored, $returned] = $this->store('data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==');
        self::assertSafeDestination($stored, 'stored return destination');
        self::assertSafeDestination($returned, 'returned destination');
    }

    public function testVbscriptUrlNeverSurvives(): void
    {
        [$stored, $returned] = $this->store('vbscript:msgbox(1)');
        self::assertSafeDestination($stored, 'stored return destination');
        self::assertSafeDestination($returned, 'returned destination');
    }
}
