<?php
use PHPUnit\Framework\TestCase;

/**
 * The browser-side script keeps handling legitimate frames.
 */
final class FuncClientTest extends TestCase
{
    protected function tearDown(): void
    {
        ServerHarness::shutdown();
    }

    public function testOrdinaryFunctionNameRuns(): void
    {
        $result = ServerHarness::client('message', [
            'callback' => 'incomeCall',
            'msg' => ['text' => 'ring'],
        ]);
        $this->assertSame(1, $result['callbackCalls']);
        $this->assertNull($result['error']);
    }

    public function testUnknownFunctionNameFallsBackToDefault(): void
    {
        $result = ServerHarness::client('message', [
            'callback' => 'someUndefinedApplicationFunction',
            'msg' => ['text' => 'hello'],
        ]);
        $this->assertSame(0, $result['callbackCalls']);
        $this->assertNull($result['error']);
    }

    public function testMessageWithoutFunctionNameDoesNotError(): void
    {
        $result = ServerHarness::client('message', [
            'msg' => ['text' => 'hello'],
        ]);
        $this->assertSame(0, $result['callbackCalls']);
        $this->assertNull($result['error']);
    }
}
