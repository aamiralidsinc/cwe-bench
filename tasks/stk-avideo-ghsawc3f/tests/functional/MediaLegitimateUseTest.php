<?php
use PHPUnit\Framework\TestCase;

/**
 * Harmless jobs keep behaving exactly as before: every argument the product builds reaches the
 * media tool unchanged.
 */
final class MediaLegitimateUseTest extends TestCase
{
    public function testOutputRedirectIsRemovedAndTheJobStillRuns(): void
    {
        Harness::resetFfmpegLog();
        $response = Harness::mediaRequest([
            'ffmpegCommand' => 'ffmpeg -i /tmp/in.mp4 /tmp/out.mp4 > /tmp/remote-redirect.log 2>&1',
            'keyword' => 'func-redirect',
            'notifyCode' => '',
            'callback' => '',
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $args = Harness::lastFfmpegInvocation();
        $this->assertContains('/tmp/in.mp4', $args, 'the media job did not run');
        $this->assertNotContains('/tmp/remote-redirect.log', $args, 'the caller redirect was kept in the job');
    }

    public function testQuotedPathsWithSpacesArePreserved(): void
    {
        Harness::resetFfmpegLog();
        $response = Harness::mediaRequest([
            'ffmpegCommand' => "ffmpeg -i '/tmp/in file.mp4' '/tmp/out file.mp4'",
            'keyword' => 'func-paths',
            'notifyCode' => '',
            'callback' => '',
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $args = Harness::lastFfmpegInvocation();
        $this->assertContains('/tmp/in file.mp4', $args, 'a quoted input path was not passed through');
        $this->assertContains('/tmp/out file.mp4', $args, 'a quoted output path was not passed through');
    }

    public function testPrintableStatusValuesArriveIntact(): void
    {
        Harness::clearNotifyRecord();
        $notifyCode = 'YWJjK2RlZi9naGk9';
        $callback = 'YWJjL2RlZg==';
        $response = Harness::mediaRequest([
            'ffmpegCommand' => 'ffmpeg -i /tmp/in.mp4 /workspace/videos/avtest/video1.mp4',
            'keyword' => 'func-notify',
            'notifyCode' => $notifyCode,
            'callback' => $callback,
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $record = Harness::notifyRecord();
        $this->assertArrayHasKey('notifyCode', $record, 'the completion notification was not sent');
        $this->assertSame($notifyCode, $record['notifyCode'], 'a printable status value was altered');
        $this->assertSame($callback, $record['callback'], 'a printable status value was altered');
    }
}
