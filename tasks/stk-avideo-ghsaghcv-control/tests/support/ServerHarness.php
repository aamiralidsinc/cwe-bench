<?php
/**
 * Shared harness for the hidden suites.
 *
 * Every suite drives the socket server's real entry points (onOpen / onMessage) with frames a
 * client would send, and observes the frames actually relayed to a second connection. The
 * browser-side checks run the platform's own client script in a small Node DOM and report
 * whether the payload executed. Nothing here re-implements the server logic under test.
 */

class LoopStub
{
    public function addTimer($interval, $callback)
    {
        return new stdClass();
    }

    public function cancelTimer($timer)
    {
    }
}

class FakeUri
{
    private $query;

    public function __construct($query)
    {
        $this->query = $query;
    }

    public function getQuery()
    {
        return $this->query;
    }
}

class FakeRequest
{
    private $query;

    public function __construct($query)
    {
        $this->query = $query;
    }

    public function getUri()
    {
        return new FakeUri($this->query);
    }
}

class FakeConnection implements \Ratchet\ConnectionInterface
{
    public $resourceId;
    public $httpRequest;
    public $sent = [];
    public $timeout = null;

    public function __construct($resourceId, $token, $selfURI = 'http://127.0.0.1:9/index.php')
    {
        $this->resourceId = $resourceId;
        $this->httpRequest = new FakeRequest(
            'webSocketToken=' . rawurlencode($token) . '&webSocketSelfURI=' . rawurlencode($selfURI)
        );
    }

    public function send($data)
    {
        $this->sent[] = $data;
    }

    public function close()
    {
    }

    public function clear()
    {
        $this->sent = [];
    }
}

final class ServerHarness
{
    private static $variant = null;
    private static $server = null;
    private static $counter = 100;
    private static $connections = [];

    public static function root(): string
    {
        return rtrim(defined('CWE_APP_ROOT') ? CWE_APP_ROOT : '/workspace', '/') . '/';
    }

    /** Build one socket server instance of the requested implementation. */
    public static function server(string $variant)
    {
        $root = self::root();
        if (self::$server !== null && self::$variant === $variant) {
            return self::$server;
        }
        if (self::$variant !== null && self::$variant !== $variant) {
            throw new RuntimeException('harness: one PHP process cannot host both server implementations');
        }
        self::$variant = $variant;
        if ($variant === 'v2') {
            if (!isset($GLOBALS['db'])) {
                require_once $root . 'plugin/YPTSocket/db.php';
                if (isset($db) && !isset($GLOBALS['db'])) {
                    $GLOBALS['db'] = $db;
                }
                // The schema module is written to run at file scope; this harness loads it
                // from a method, so publish the variables its helpers read through `global`.
                if (isset($ignoreColumns)) {
                    $GLOBALS['ignoreColumns'] = $ignoreColumns;
                }
            }
            require_once $root . 'plugin/YPTSocket/MessageSQLiteV2.php';
            self::$server = new \Socket\Message();
        } else {
            require_once $root . 'plugin/YPTSocket/Message.php';
            self::$server = new \Socket\Message(new LoopStub());
        }
        return self::$server;
    }

    /** Mint an encrypted connection token exactly as the platform's token endpoint does. */
    public static function token(array $options = []): string
    {
        $usersId = isset($options['users_id']) ? (int)$options['users_id'] : 0;
        $msg = new stdClass();
        $msg->isCommandLineInterface = !empty($options['cli']);
        $msg->sentFrom = isset($options['sentFrom']) ? $options['sentFrom'] : 'browser';
        $msg->from_users_id = $usersId;
        $msg->isAdmin = false;
        $msg->user_name = isset($options['name']) ? $options['name'] : ('user' . $usersId);
        $msg->browser = 'chrome';
        $msg->os = 'linux';
        $msg->yptDeviceId = isset($options['device'])
            ? $options['device']
            : ('ypt-chrome-linux-127_0_0_1-curl-' . $usersId);
        $msg->token = getToken(43200);
        $msg->time = time();
        $msg->ip = '127.0.0.1';
        $msg->send_to_uri_pattern = '';
        $msg->selfURI = isset($options['selfURI']) ? $options['selfURI'] : 'http://127.0.0.1:9/index.php';
        $msg->videos_id = 0;
        $msg->live_key = isset($options['live_key']) ? $options['live_key'] : false;
        $msg->location = false;
        return encryptString(json_encode($msg));
    }

    public static function connect($server, string $token, string $selfURI = 'http://127.0.0.1:9/index.php'): FakeConnection
    {
        $connection = new FakeConnection(self::$counter++, $token, $selfURI);
        $server->onOpen($connection);
        self::$connections[] = [$server, $connection];
        return $connection;
    }

    public static function send($server, FakeConnection $from, array $frame): void
    {
        $server->onMessage($from, json_encode($frame));
    }

    /** The last frame a connection received, decoded as an array. */
    public static function lastFrame(FakeConnection $connection): array
    {
        if (!$connection->sent) {
            return [];
        }
        $decoded = json_decode($connection->sent[count($connection->sent) - 1], true);
        return is_array($decoded) ? $decoded : [];
    }

    /** The payload the receiving client would hand to its callback. */
    public static function lastPayload(FakeConnection $connection)
    {
        $frame = self::lastFrame($connection);
        return array_key_exists('msg', $frame) ? $frame['msg'] : null;
    }

    public static function frameHasKey($data, string $key): bool
    {
        if (is_object($data)) {
            $data = json_decode(json_encode($data), true);
        }
        if (!is_array($data)) {
            return false;
        }
        if (array_key_exists($key, $data)) {
            return true;
        }
        foreach ($data as $value) {
            if (self::frameHasKey($value, $key)) {
                return true;
            }
        }
        return false;
    }

    /** Run the platform's client script against one frame and report what executed. */
    public static function client(string $mode, array $frame): array
    {
        return self::node('js_harness.js', ['mode' => $mode, 'frame' => $frame], [
            'SOCKET_SCRIPT' => self::root() . 'plugin/YPTSocket/script.js',
        ]);
    }

    /** Run the platform's call-notification script against one payload. */
    public static function caller(array $payload, int $myUsersId): array
    {
        return self::node('caller_harness.js', ['frame' => $payload, 'myUsersId' => $myUsersId], [
            'CALLER_SCRIPT' => self::root() . 'plugin/WebRTC/call/caller.js',
        ]);
    }

    private static function node(string $script, array $payload, array $env = []): array
    {
        $command = ['node', __DIR__ . '/' . $script];
        $descriptors = [
            0 => ['pipe', 'r'],
            1 => ['pipe', 'w'],
            2 => ['pipe', 'w'],
        ];
        $environment = array_merge([
            'PATH' => '/usr/local/bin:/usr/bin:/bin',
            'HOME' => '/tmp',
            'LANG' => 'C.UTF-8',
        ], $env);
        $process = proc_open($command, $descriptors, $pipes, dirname(__DIR__), $environment);
        if (!is_resource($process)) {
            throw new RuntimeException('harness: cannot start node');
        }
        fwrite($pipes[0], json_encode($payload));
        fclose($pipes[0]);
        $stdout = stream_get_contents($pipes[1]);
        $stderr = stream_get_contents($pipes[2]);
        fclose($pipes[1]);
        fclose($pipes[2]);
        proc_close($process);
        $decoded = json_decode((string)$stdout, true);
        if (!is_array($decoded)) {
            throw new RuntimeException('harness: client script produced no result (' . trim((string)$stderr) . ')');
        }
        return $decoded;
    }

    public static function shutdown(): void
    {
        foreach (self::$connections as $entry) {
            list($server, $connection) = $entry;
            try {
                $server->onClose($connection);
            } catch (\Throwable $e) {
                // A closed connection is enough; the next test uses fresh identifiers.
            }
        }
        self::$connections = [];
        if (class_exists('React\\EventLoop\\Loop')) {
            React\EventLoop\Loop::stop();
        }
    }
}
