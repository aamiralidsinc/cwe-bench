<?php
use PHPUnit\Framework\TestCase;

/**
 * A client identifier becomes part of the path the restream job logs to.
 */
final class RestreamLogTest extends TestCase
{
    public function testUserIdentifierCannotStartAnotherCommand(): void
    {
        $marker = Harness::marker('restreamuser');
        $response = Harness::restreamRequest([
            'type' => 'start',
            'token' => 'harness-token',
            'm3u8' => 'http://127.0.0.1:' . Harness::$stubPort . '/stream.m3u8',
            'restreamsDestinations' => ['rtmp://127.0.0.1/live/key'],
            'users_id' => "uid;touch $marker;",
            'live_restreams_id' => 1,
            'liveTransmitionHistory_id' => 601,
        ]);
        $this->assertGreaterThan(0, $response[0], 'the restream endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(1500);
        $this->assertFileDoesNotExist($marker, 'a user identifier started another command');
    }
}
