<?php
use PHPUnit\Framework\TestCase;

/**
 * The reported route: the command text a job carries must not be able to background the media
 * command and start another program on the host.
 */
final class CommandShellTest extends TestCase
{
    private function assertBlocked(string $command, string $name): void
    {
        $marker = Harness::marker($name);
        $response = Harness::mediaRequest([
            'ffmpegCommand' => str_replace('{marker}', $marker, $command),
            'keyword' => 'ctl-' . $name,
            'notifyCode' => 'a2V5',
            'callback' => '',
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(2500);
        $this->assertFileDoesNotExist($marker, 'a separator in the command started another command');
    }

    public function testSeparatorCannotStartAnotherCommand(): void
    {
        $this->assertBlocked('ffmpeg -i /tmp/in.mp4 /tmp/out.mp4 & touch {marker} #', 'separator');
    }

    public function testSeparatorWithoutASpaceCannotStartAnotherCommand(): void
    {
        $this->assertBlocked('ffmpeg -i /tmp/in.mp4 /tmp/out.mp4 &touch {marker} #', 'separator-nospace');
    }

    public function testSeparatorBeforeTheInputCannotStartAnotherCommand(): void
    {
        $this->assertBlocked('ffmpeg & touch {marker} # -i /tmp/in.mp4 /tmp/out.mp4', 'separator-early');
    }

    public function testSeparatorAfterAQuotedArgumentCannotStartAnotherCommand(): void
    {
        $this->assertBlocked('ffmpeg -i "/tmp/in file.mp4" /tmp/out.mp4 & touch {marker} #', 'separator-quoted');
    }
}
