<?php
declare(strict_types=1);

/**
 * Runs one reader call in a fresh PHP process.
 *
 * Several failures in this task are resource failures (an unbounded decompression or an endless
 * chain walk), so a call made inside the test process would take the whole suite down. Each case
 * is therefore driven in its own process under a memory cap and a wall-clock timeout. A refusal
 * is a completion with the REFUSED marker; a fatal error, a kill for running out of memory, or a
 * timeout is not a refusal.
 */
final class Harness
{
    /**
     * @return array{rc: int, out: string}
     */
    public static function probe(string $mode, string $fixture, int $memoryMb = 64, int $timeoutSec = 12): array
    {
        $cmd = sprintf(
            'timeout -k 2 %d %s -d memory_limit=%dM -d display_errors=stderr %s %s %s %s 2>&1',
            $timeoutSec,
            escapeshellarg(PHP_BINARY),
            $memoryMb,
            escapeshellarg(__DIR__ . '/probe.php'),
            escapeshellarg(getenv('PPS_AUTOLOAD') ?: '/workspace/vendor/autoload.php'),
            escapeshellarg($mode),
            escapeshellarg(__DIR__ . '/fixtures/' . $fixture)
        );
        $lines = [];
        $rc = 0;
        exec($cmd, $lines, $rc);

        return ['rc' => $rc, 'out' => implode("\n", $lines)];
    }

    public static function assertRefused(string $mode, string $fixture, int $memoryMb = 64): void
    {
        $r = self::probe($mode, $fixture, $memoryMb);
        \PHPUnit\Framework\Assert::assertSame(
            0,
            $r['rc'],
            "the call did not finish with a handled error (exit {$r['rc']}): " . $r['out']
        );
        \PHPUnit\Framework\Assert::assertStringContainsString(
            'REFUSED',
            $r['out'],
            'the supplied file was not refused: ' . $r['out']
        );
        \PHPUnit\Framework\Assert::assertStringNotContainsString(
            'PROCEEDED',
            $r['out'],
            'the supplied file was accepted: ' . $r['out']
        );
    }
}
