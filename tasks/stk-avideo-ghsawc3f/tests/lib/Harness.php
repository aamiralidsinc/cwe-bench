<?php
/**
 * Shared harness for the hidden suites.
 *
 * Boots two loopback-only PHP servers: the application under test (from /workspace) and a small
 * stand-in for the main platform site that answers the decrypt, API-secret, token and notify
 * calls the application makes. Nothing here imports product code; every suite drives a real HTTP
 * entry point and observes the side effects of what actually ran.
 */

final class Harness
{
    public const ROOT = '/workspace';

    public static $appPort = 0;
    public static $stubPort = 0;

    public static $ffmpegLog = '/tmp/avi-ffmpeg-args.log';
    public static $stubLog = '/tmp/avi-stub-requests.jsonl';
    public static $notifyLog = '/tmp/avi-notify.json';

    private static $procs = [];
    private static $booted = false;

    public static function boot(): void
    {
        if (self::$booted) {
            return;
        }
        self::$appPort = self::freePort();
        self::$stubPort = self::freePort();

        if (!is_dir(self::ROOT . '/videos')) {
            @mkdir(self::ROOT . '/videos', 0775, true);
        }
        $config = "<?php\n"
            . "\$global['webSiteRootURL'] = 'http://127.0.0.1:" . self::$stubPort . "/';\n"
            . "\$GLOBALS['streamerURL'] = 'http://127.0.0.1:" . self::$stubPort . "/';\n";
        if (file_put_contents(self::ROOT . '/videos/standalone.configuration.php', $config) === false) {
            throw new RuntimeException('harness: cannot write the standalone configuration');
        }
        @unlink(self::ROOT . '/videos/configuration.php');
        @unlink(self::$ffmpegLog);
        @unlink(self::$stubLog);
        @unlink(self::$notifyLog);

        $env = [
            'PATH' => '/usr/local/bin:/usr/bin:/bin',
            'HOME' => '/home/agent',
            'LANG' => 'C.UTF-8',
            'LC_ALL' => 'C.UTF-8',
            'TZ' => 'UTC',
            'AVI_FFMPEG_LOG' => self::$ffmpegLog,
        ];
        self::spawn([PHP_BINARY, '-S', '127.0.0.1:' . self::$stubPort, __DIR__ . '/stub.php'], $env, '/tmp/avi-stub-server.out');
        self::spawn(
            [PHP_BINARY, '-S', '127.0.0.1:' . self::$appPort, '-t', self::ROOT,
             '-d', 'display_errors=0', '-d', 'error_reporting=0', '-d', 'log_errors=1'],
            $env,
            '/tmp/avi-app-server.out'
        );
        self::waitForPort(self::$stubPort);
        self::waitForPort(self::$appPort);
        self::$booted = true;
        register_shutdown_function([self::class, 'shutdown']);
    }

    public static function shutdown(): void
    {
        foreach (self::$procs as $proc) {
            if (is_resource($proc)) {
                @proc_terminate($proc, 9);
                @proc_close($proc);
            }
        }
        self::$procs = [];
    }

    private static function freePort(): int
    {
        $sock = @stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
        if (!$sock) {
            throw new RuntimeException("harness: cannot reserve a port ($errstr)");
        }
        $name = stream_socket_get_name($sock, false);
        fclose($sock);
        return (int)substr($name, strrpos($name, ':') + 1);
    }

    private static function spawn(array $command, array $env, string $log): void
    {
        $descriptors = [
            0 => ['file', '/dev/null', 'r'],
            1 => ['file', $log, 'a'],
            2 => ['file', $log, 'a'],
        ];
        $proc = proc_open($command, $descriptors, $pipes, self::ROOT, $env);
        if (!is_resource($proc)) {
            throw new RuntimeException('harness: cannot start ' . implode(' ', $command));
        }
        self::$procs[] = $proc;
    }

    private static function waitForPort(int $port): void
    {
        $deadline = microtime(true) + 15;
        while (microtime(true) < $deadline) {
            $fp = @fsockopen('127.0.0.1', $port, $errno, $errstr, 0.2);
            if ($fp) {
                fclose($fp);
                return;
            }
            usleep(100000);
        }
        throw new RuntimeException("harness: server on port $port did not start");
    }

    // ---- requests ---------------------------------------------------------------------

    private static function request(string $path, string $body, string $type, int $timeout): array
    {
        $ch = curl_init('http://127.0.0.1:' . self::$appPort . $path);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $body,
            CURLOPT_HTTPHEADER => ['Content-Type: ' . $type],
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT => $timeout,
        ]);
        $response = curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        return [$code, is_string($response) ? $response : ''];
    }

    public static function postForm(string $path, array $fields, int $timeout = 30): array
    {
        return self::request($path, http_build_query($fields), 'application/x-www-form-urlencoded', $timeout);
    }

    public static function postJson(string $path, array $body, int $timeout = 90): array
    {
        return self::request($path, json_encode($body), 'application/json', $timeout);
    }

    /**
     * Send a job to the standalone media endpoint the way the main site does: the payload is
     * handed over as an opaque encrypted blob, which the harness's platform stand-in decrypts.
     */
    public static function mediaRequest(array $payload, int $timeout = 30): array
    {
        $payload['time'] = time();
        $encrypted = base64_encode(json_encode($payload));
        return self::postForm(
            '/plugin/API/standAlone/ffmpeg.json.php',
            ['APISecret' => 'harness-secret', 'codeToExecEncrypted' => $encrypted],
            $timeout
        );
    }

    public static function restreamRequest(array $body, int $timeout = 90): array
    {
        return self::postJson('/plugin/Live/standAloneFiles/restreamer.json.php', $body, $timeout);
    }

    /** Pull the JSON object out of a response that may also carry PHP notices. */
    public static function json(array $response)
    {
        $body = $response[1];
        $start = strpos($body, '{');
        if ($start === false) {
            return null;
        }
        $decoded = json_decode(substr($body, $start), true);
        return is_array($decoded) ? $decoded : null;
    }

    // ---- observations -----------------------------------------------------------------

    public static function marker(string $name): string
    {
        $path = '/tmp/avi-marker-' . preg_replace('/[^A-Za-z0-9_-]/', '', $name);
        @unlink($path);
        return $path;
    }

    public static function sleep(int $milliseconds): void
    {
        usleep($milliseconds * 1000);
    }

    public static function waitForFile(string $path, int $milliseconds = 8000): bool
    {
        $deadline = microtime(true) + $milliseconds / 1000;
        while (microtime(true) < $deadline) {
            clearstatcache(true, $path);
            if (is_file($path) && filesize($path) > 0) {
                return true;
            }
            usleep(100000);
        }
        return false;
    }

    public static function resetFfmpegLog(): void
    {
        @unlink(self::$ffmpegLog);
    }

    /** The argument vector of the most recent media-tool invocation (empty when none ran). */
    public static function lastFfmpegInvocation(int $milliseconds = 8000): array
    {
        self::waitForFile(self::$ffmpegLog, $milliseconds);
        // Let a second writer finish before reading.
        usleep(150000);
        if (!is_file(self::$ffmpegLog)) {
            return [];
        }
        $parts = preg_split('/^---$/m', (string)file_get_contents(self::$ffmpegLog));
        for ($i = count($parts) - 1; $i >= 0; $i--) {
            $args = array_values(array_filter(explode("\n", trim($parts[$i])), 'strlen'));
            if ($args) {
                return $args;
            }
        }
        return [];
    }

    public static function stubRequests(): array
    {
        if (!is_file(self::$stubLog)) {
            return [];
        }
        $out = [];
        foreach (file(self::$stubLog, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $decoded = json_decode($line, true);
            if (is_array($decoded)) {
                $out[] = $decoded;
            }
        }
        return $out;
    }

    public static function notifyRecord(): array
    {
        self::waitForFile(self::$notifyLog, 8000);
        if (!is_file(self::$notifyLog)) {
            return [];
        }
        $decoded = json_decode((string)file_get_contents(self::$notifyLog), true);
        return is_array($decoded) ? $decoded : [];
    }

    public static function clearNotifyRecord(): void
    {
        @unlink(self::$notifyLog);
    }
}
