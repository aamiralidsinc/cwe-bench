<?php
use PHPUnit\Framework\TestCase;

/**
 * Values that the job carries beside the command text are placed on the same command line.
 */
final class NotifyValueTest extends TestCase
{
    private function jobWithVideoPath(): array
    {
        return [
            'ffmpegCommand' => 'ffmpeg -i /tmp/in.mp4 /workspace/videos/avtest/video1.mp4',
            'keyword' => 'sec-notify',
        ];
    }

    public function testNotifyCodeCannotStartAnotherCommand(): void
    {
        $marker = Harness::marker('notifycode');
        $payload = $this->jobWithVideoPath();
        $payload['notifyCode'] = ";touch $marker;";
        $payload['callback'] = '';
        $response = Harness::mediaRequest($payload);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(2500);
        $this->assertFileDoesNotExist($marker, 'a notification value started another command');
    }

    public function testCallbackCannotStartAnotherCommand(): void
    {
        $marker = Harness::marker('callback');
        $payload = $this->jobWithVideoPath();
        $payload['notifyCode'] = 'a2V5';
        $payload['callback'] = ";touch $marker;";
        $response = Harness::mediaRequest($payload);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(2500);
        $this->assertFileDoesNotExist($marker, 'a callback value started another command');
    }
}
