<?php
use PHPUnit\Framework\TestCase;

/**
 * The command text a job carries must not be able to start another program on the media host.
 */
final class CommandShellTest extends TestCase
{
    public function testSeparatorCannotStartAnotherCommand(): void
    {
        $marker = Harness::marker('separator');
        $response = Harness::mediaRequest([
            'ffmpegCommand' => "ffmpeg -i /tmp/in.mp4 /tmp/out.mp4 & touch $marker #",
            'keyword' => 'sec-separator',
            'notifyCode' => 'a2V5',
            'callback' => '',
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(2500);
        $this->assertFileDoesNotExist($marker, 'a separator in the command started another command');
    }

    public function testCommandSubstitutionCannotStartAnotherCommand(): void
    {
        $marker = Harness::marker('substitution');
        $response = Harness::mediaRequest([
            'ffmpegCommand' => "ffmpeg -i /tmp/in.mp4 $(touch $marker) /tmp/out.mp4",
            'keyword' => 'sec-substitution',
            'notifyCode' => 'a2V5',
            'callback' => '',
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(2500);
        $this->assertFileDoesNotExist($marker, 'command substitution in the command ran');
    }

    public function testNewlineCannotStartAnotherCommand(): void
    {
        $marker = Harness::marker('newline');
        $response = Harness::mediaRequest([
            'ffmpegCommand' => "ffmpeg -i /tmp/in.mp4 /tmp/out.mp4\ntouch $marker #",
            'keyword' => 'sec-newline',
            'notifyCode' => 'a2V5',
            'callback' => '',
        ]);
        $this->assertGreaterThan(0, $response[0], 'the media endpoint did not answer');
        $this->assertTrue(Harness::json($response) !== null || $response[0] >= 400, 'the endpoint returned neither a result nor a client error');
        Harness::sleep(2500);
        $this->assertFileDoesNotExist($marker, 'a newline in the command started another command');
    }
}
