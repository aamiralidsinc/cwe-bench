<?php
use PHPUnit\Framework\TestCase;

/**
 * Job-tracking requests look processes up by a value the client supplies.
 */
final class ProcessLookupTest extends TestCase
{
    public function testListLookupValueCannotStartAnotherCommand(): void
    {
        $marker = Harness::marker('listlookup');
        $response = Harness::mediaRequest([
            'list' => 1,
            'keyword' => "x'; touch $marker; echo '",
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(2500);
        $this->assertFileDoesNotExist($marker, 'a list lookup value started another command');
    }

    public function testRunningLookupValueCannotStartAnotherCommand(): void
    {
        $marker = Harness::marker('runninglookup');
        $response = Harness::mediaRequest([
            'isKeywordRunning' => "y'; touch $marker; echo '",
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(2500);
        $this->assertFileDoesNotExist($marker, 'a running lookup value started another command');
    }
}
