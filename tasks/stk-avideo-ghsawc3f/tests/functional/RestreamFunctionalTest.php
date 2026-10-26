<?php
use PHPUnit\Framework\TestCase;

/**
 * Ordinary restreams still start, still keep the stream URL's query parameters, and still log
 * under the user that asked for them.
 */
final class RestreamFunctionalTest extends TestCase
{
    private function cleanLogs(string $usersId, int $historyId): void
    {
        foreach (glob("/var/www/tmp/ffmpeg_restreamer_{$usersId}_*_0_{$historyId}_*") ?: [] as $file) {
            @unlink($file);
        }
    }

    private function restream(string $usersId, int $historyId): array
    {
        $this->cleanLogs($usersId, $historyId);
        Harness::resetFfmpegLog();
        $response = Harness::restreamRequest([
            'type' => 'start',
            'token' => 'harness-token',
            'm3u8' => 'http://127.0.0.1:' . Harness::$stubPort . '/stream.m3u8',
            'restreamsDestinations' => ['rtmp://127.0.0.1/live/key'],
            'users_id' => $usersId,
            'live_restreams_id' => 1,
            'liveTransmitionHistory_id' => $historyId,
        ]);
        $this->assertGreaterThan(0, $response[0], 'the restream endpoint did not answer');
        return $response;
    }

    private function assertRestreamRan(array $response, string $usersId, int $historyId): void
    {
        $json = Harness::json($response);
        $this->assertIsArray($json, 'the restream request did not return a JSON object');
        $this->assertArrayHasKey('error', $json, 'the restream answer lacks its result');
        $this->assertFalse($json['error'], 'a legitimate restream was refused');

        $args = Harness::lastFfmpegInvocation();
        $streamUrl = 'http://127.0.0.1:' . Harness::$stubPort
            . '/stream.m3u8?live_restreams_id=0&liveTransmitionHistory_id=' . $historyId;
        $this->assertContains($streamUrl, $args, 'the restream input lost its separator or query parameters');
        $this->assertContains('rtmp://127.0.0.1/live/key', $args, 'the restream destination was not passed through');

        $this->assertNotEmpty(
            glob("/var/www/tmp/ffmpeg_restreamer_{$usersId}_*_0_{$historyId}_*") ?: [],
            'the restream log was not created for the requesting user'
        );
    }

    public function testRestreamForAWebUserStillWorks(): void
    {
        $response = $this->restream('web', 701);
        $this->assertRestreamRan($response, 'web', 701);
    }

    public function testRestreamForANumericUserStillWorks(): void
    {
        $response = $this->restream('4242', 702);
        $this->assertRestreamRan($response, '4242', 702);
    }
}
