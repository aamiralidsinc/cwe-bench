<?php
/**
 * Hidden-suite harness for Flarum. Boots the restored /workspace application against a local
 * MariaDB test site, sends PSR-7 requests through the real request handler, and offers the
 * shared assertions. It deliberately implements its own extenders so that nothing in the
 * agent-writable repository controls the harness bookkeeping.
 */

define('H_ROOT', '/workspace/framework/core');
define('H_SITE', '/workspace/.htests/site');
define('H_CANARY_DIR', '/workspace/.htests');
define('H_DB_HOST', '127.0.0.1');
define('H_DB_PORT', 3306);
define('H_DB_NAME', 'flarum_test');
define('H_DB_USER', 'flarum');
define('H_DB_PASS', 'flarumpass');

require H_ROOT . '/vendor/autoload.php';

use Flarum\Extend\ExtenderInterface;
use Flarum\Extension\Extension;
use Flarum\Foundation\Config;
use Flarum\Foundation\InstalledSite;
use Flarum\Foundation\Paths;
use Flarum\Settings\SettingsRepositoryInterface;
use Illuminate\Contracts\Container\Container;
use Illuminate\Database\ConnectionInterface;
use Illuminate\Support\Str;
use Laminas\Diactoros\CallbackStream;
use Laminas\Diactoros\ServerRequest;
use Carbon\Carbon;

/** Opens one database transaction for the case; the connection close rolls it back. */
class HarnessTransaction implements ExtenderInterface
{
    public function extend(Container $container, Extension $extension = null)
    {
        $db = $container->make(ConnectionInterface::class);
        $db->beginTransaction();
        $GLOBALS['h_db'] = $db;
    }
}

/** Applies the case's pre-boot settings, as the project's own test harness does. */
class HarnessSettings implements ExtenderInterface
{
    protected $settings;

    public function __construct(array $settings)
    {
        $this->settings = $settings;
    }

    public function extend(Container $container, Extension $extension = null)
    {
        if (! count($this->settings)) {
            return;
        }

        $repository = $container->make(SettingsRepositoryInterface::class);

        foreach ($this->settings as $key => $value) {
            $repository->set($key, $value);
        }
    }
}

/**
 * Boots the application. Extenders are applied in order, after the transaction extender.
 *
 * @param ExtenderInterface[] $extenders
 * @param array $settings pre-boot settings
 */
function h_boot(array $extenders = [], array $settings = [])
{
    clearstatcache(true);

    $config = include H_SITE . '/config.php';

    $site = new InstalledSite(
        new Paths([
            'base' => H_SITE,
            'public' => H_SITE . '/public',
            'storage' => H_SITE . '/storage',
            'vendor' => H_ROOT . '/vendor',
        ]),
        new Config($config)
    );

    $site->extendWith(array_merge([
        new HarnessTransaction(),
        new HarnessSettings($settings),
    ], $extenders));

    $GLOBALS['h_app'] = $site->bootApp();

    return $GLOBALS['h_app'];
}

function h_db()
{
    if (empty($GLOBALS['h_db'])) {
        fwrite(STDERR, "FAIL: the harness database connection was not opened\n");
        exit(1);
    }

    return $GLOBALS['h_db'];
}

function h_request(string $method, string $path, $json = null, $asUser = null)
{
    $request = new ServerRequest([], [], $path, $method);

    if ($json !== null) {
        $request = $request
            ->withHeader('Content-Type', 'application/json')
            ->withBody(new CallbackStream(function () use ($json) {
                return json_encode($json);
            }));
    }

    if ($asUser !== null) {
        $token = Str::random(40);
        h_db()->table('access_tokens')->insert([
            'token' => $token,
            'user_id' => $asUser,
            'created_at' => Carbon::now()->toDateTimeString(),
            'last_activity_at' => Carbon::now()->toDateTimeString(),
            'type' => 'session',
        ]);
        $request = $request->withAddedHeader('Authorization', "Token {$token}");
    }

    return $request;
}

function h_send($request)
{
    return $GLOBALS['h_app']->getRequestHandler()->handle($request);
}

function h_setting(string $key)
{
    return h_db()->table('settings')->where('key', $key)->value('value');
}

/** Writes a fresh marker file and returns its path. */
function h_canary(string $token): string
{
    $path = H_CANARY_DIR . '/canary_' . bin2hex(random_bytes(6)) . '.txt';
    if (file_put_contents($path, $token) === false) {
        fwrite(STDERR, "FAIL: cannot write the marker file\n");
        exit(1);
    }

    return $path;
}

function h_assets_reset(): void
{
    foreach (['/public/assets', '/storage/less'] as $dir) {
        foreach (glob(H_SITE . $dir . '/*') ?: [] as $file) {
            @unlink($file);
        }
    }
}

function h_css(): string
{
    $path = H_SITE . '/public/assets/forum.css';

    return is_file($path) ? (string) file_get_contents($path) : '';
}

function h_check(bool $ok, string $message): void
{
    if (! $ok) {
        fwrite(STDERR, "FAIL: {$message}\n");
        exit(1);
    }
}

/**
 * Shared assertion for a value that must not make the compiler read a local file.
 *
 * A correct fix may refuse the save (a client error, nothing stored) or neutralise the value
 * (a successful save whose generated stylesheet is clean); either outcome is accepted.
 */
function h_assert_no_read($response, string $key, string $payload, string $needle): void
{
    $status = (int) $response->getStatusCode();

    if ($status >= 200 && $status < 300) {
        $rendered = h_send(h_request('GET', '/'));
        h_check((int) $rendered->getStatusCode() === 200,
            "the forum still builds its stylesheet after the save (got {$rendered->getStatusCode()})");
        h_check(strpos(h_css(), $needle) === false,
            'the submitted value did not make the stylesheet contain the local file');
        return;
    }

    h_check($status >= 400 && $status < 500, "a refused value is reported as a client error (got {$status})");
    h_check(h_setting($key) !== $payload, 'a refused value is not stored');
    h_check(strpos(h_css(), $needle) === false, 'a refused value did not publish the local file');
}

/** Starts a marker HTTP server on loopback; returns [process, port, hits file]. */
function h_listener_start(): array
{
    $port = 18000 + random_int(0, 999);
    $hits = H_CANARY_DIR . '/hits_' . bin2hex(random_bytes(4)) . '.log';
    file_put_contents($hits, '');

    $router = __DIR__ . '/router.php';
    $cmd = escapeshellarg(PHP_BINARY) . ' -S 127.0.0.1:' . $port . ' ' . escapeshellarg($router);
    $process = proc_open($cmd, [
        0 => ['file', '/dev/null', 'r'],
        1 => ['file', '/dev/null', 'w'],
        2 => ['file', '/dev/null', 'w'],
    ], $pipes, null, ['HARNESS_HITS' => $hits, 'PATH' => getenv('PATH') ?: '/usr/bin:/bin']);

    // Wait until the server answers a readiness request, so a listener that never came up
    // cannot make the assertion pass for the wrong reason.
    $ready = false;
    for ($i = 0; $i < 100; $i++) {
        $socket = @stream_socket_client('tcp://127.0.0.1:' . $port, $errno, $errstr, 0.2);
        if ($socket) {
            fwrite($socket, "GET /__ready HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n");
            stream_set_timeout($socket, 1);
            $answer = (string) fread($socket, 512);
            fclose($socket);
            if (strpos($answer, '200') !== false) {
                $ready = true;
                break;
            }
        }
        usleep(50000);
    }

    if (! $ready) {
        fwrite(STDERR, "FAIL: the marker HTTP listener did not start\n");
        exit(1);
    }

    file_put_contents($hits, '');

    return [$process, $port, $hits];
}

function h_listener_hits(string $hits): int
{
    $lines = @file($hits, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);

    return is_array($lines) ? count($lines) : 0;
}

function h_listener_stop($process): void
{
    if (is_resource($process)) {
        $status = proc_get_status($process);
        if ($status['running']) {
            proc_terminate($process, 9);
        }
        proc_close($process);
    }
}

/** A random marker token that cannot occur in the shipped stylesheet. */
function h_token(string $prefix = 'MARK'): string
{
    return $prefix . bin2hex(random_bytes(10));
}
