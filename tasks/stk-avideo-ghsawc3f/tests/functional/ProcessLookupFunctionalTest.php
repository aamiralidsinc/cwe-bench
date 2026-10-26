<?php
use PHPUnit\Framework\TestCase;

/**
 * Ordinary job-tracking requests keep answering.
 */
final class ProcessLookupFunctionalTest extends TestCase
{
    public function testListOfRunningJobsAnswers(): void
    {
        $response = Harness::mediaRequest(['list' => 1, 'keyword' => 'legitkw-1']);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $json = Harness::json($response);
        $this->assertIsArray($json, 'the list request did not return a JSON object');
        $this->assertArrayHasKey('list', $json, 'the list request returned no job list');
        $this->assertIsArray($json['list'], 'the job list is not an array');
    }

    public function testRunningStateAnswers(): void
    {
        $response = Harness::mediaRequest(['isKeywordRunning' => 'legitkw-1']);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $json = Harness::json($response);
        $this->assertIsArray($json, 'the running-state request did not return a JSON object');
        $this->assertArrayHasKey('isRunning', $json, 'the running-state answer lacks its result');
        $this->assertFalse($json['isRunning'], 'no job with that value should be reported as running');
    }
}
