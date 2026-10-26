<?php

namespace BsBench;

use Spatie\Browsershot\Browsershot;

/**
 * Shared plumbing for the hidden suites. Everything here is test bookkeeping: the offline
 * renderer double stands in for the browser engine and records the local paths it opens.
 */
final class Support
{
    public static function supportDir(): string
    {
        return __DIR__;
    }

    /** Point a Browsershot instance at the offline renderer double. */
    public static function offline(Browsershot $browsershot): Browsershot
    {
        return $browsershot
            ->setNodeBinary(__DIR__.'/fake-node')
            ->setNodeModulePath(__DIR__);
    }

    /**
     * Create a directory holding a local file whose content is a fresh marker.
     *
     * @return array{0: string, 1: string, 2: string} [directory, file path, marker]
     */
    public static function victim(): array
    {
        $dir = self::tempDir('victim');
        mkdir($dir.'/files', 0700, true);
        $marker = 'LOCAL-'.bin2hex(random_bytes(8));
        $path = $dir.'/files/secret.txt';
        file_put_contents($path, $marker);

        return [$dir, $path, $marker];
    }

    public static function tempDir(string $prefix): string
    {
        $dir = sys_get_temp_dir().'/bs-'.$prefix.'-'.bin2hex(random_bytes(8));
        mkdir($dir, 0700, true);

        return $dir;
    }

    public static function htmlFile(string $html): string
    {
        $dir = self::tempDir('html');
        $path = $dir.'/page.html';
        file_put_contents($path, $html);

        return $path;
    }

    /**
     * Run one rendering call and collect what it produced and which local paths the
     * renderer opened.
     *
     * @return array{threw: bool, body: string, reads: string, output: string, log: string}
     */
    public static function render(callable $call): array
    {
        $dir = self::tempDir('run');
        $output = $dir.'/out.png';
        $log = $dir.'/reads.log';
        putenv('BS_TEST_LOG='.$log);

        $threw = false;
        try {
            $call($output);
        } catch (\Throwable $e) {
            $threw = true;
        }

        $body = is_file($output) ? (string) file_get_contents($output) : '';
        $reads = is_file($log) ? (string) file_get_contents($log) : '';

        return ['threw' => $threw, 'body' => $body, 'reads' => $reads, 'output' => $output, 'log' => $log];
    }

    /** Remove the scratch tree of one run, best effort. */
    public static function cleanup(string ...$paths): void
    {
        foreach ($paths as $path) {
            if ($path === '') {
                continue;
            }
            if (is_dir($path)) {
                foreach (scandir($path) ?: [] as $entry) {
                    if ($entry === '.' || $entry === '..') {
                        continue;
                    }
                    $child = $path.'/'.$entry;
                    is_dir($child) ? self::cleanup($child) : @unlink($child);
                }
                @rmdir($path);
            } else {
                @unlink($path);
            }
        }
    }
}
