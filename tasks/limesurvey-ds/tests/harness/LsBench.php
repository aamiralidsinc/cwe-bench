<?php

namespace LsBench;

use PDO;

/**
 * Small HTTP client for the running application. Cookies are tracked by hand so
 * a test can send the same session over a request with a different Host header.
 */
class Client
{
    public const BASE = 'http://127.0.0.1:8080/index.php';
    public const LEGIT_HOST = '127.0.0.1:8080';
    public const PUBLIC_HOST = 'trusted.example';
    public const PUBLIC_URL = 'https://trusted.example/limesurvey';
    public const SURVEY_ID = 186734;
    public const PARTICIPANT_TOKEN = 'PARTTOKEN001';
    public const ADMIN_USER = 'admin';
    public const ADMIN_PASS = 'password';
    public const ADMIN_EMAIL = 'admin@example.org';
    public const BATCH_UID = 2;
    public const BATCH_EMAIL = 'batchuser@example.org';
    public const MAIL_DIR = '/tmp/lsmail';
    public const ALLOWED_HOSTS_FILE = '/workspace/application/config/allowed_hosts.php';

    public int $status = 0;
    public string $body = '';
    public array $headers = [];
    public string $transportError = '';
    public string $host;

    private array $cookies = [];

    public function __construct(string $host = self::LEGIT_HOST)
    {
        $this->host = $host;
    }

    public function get(string $route, ?string $host = null, array $extraHeaders = []): void
    {
        $this->send('GET', $route, null, $host, $extraHeaders);
    }

    public function post(string $route, array $data, ?string $host = null, array $extraHeaders = []): void
    {
        $this->send('POST', $route, $data, $host, $extraHeaders);
    }

    /** Send a JSON-RPC request body to an API route. */
    public function postJson(string $route, array $payload, ?string $host = null, array $extraHeaders = []): void
    {
        $this->send('POST', $route, $payload, $host, array_merge(['Content-Type: application/json'], $extraHeaders), true);
    }

    /**
     * Fetch the form page from the server's own address, remember its CSRF
     * token, then submit to $route with the host under test. Keeping the form
     * fetch legitimate means a session/CSRF blocker is not mistaken for a fix.
     */
    public function submitForm(string $route, string $formRoute, array $data, ?string $postHost = null): void
    {
        $this->get($formRoute, self::LEGIT_HOST);
        $token = $this->csrfToken();
        if ($token !== null) {
            $this->cookies['YII_CSRF_TOKEN'] = $token;
            $data['YII_CSRF_TOKEN'] = $token;
        }
        $this->post($route, $data, $postHost);
    }

    public function login(string $user = self::ADMIN_USER, string $password = self::ADMIN_PASS, ?string $host = null): void
    {
        $this->get('?r=admin/authentication/sa/login', $host);
        $token = $this->csrfToken();
        if ($token !== null) {
            $this->cookies['YII_CSRF_TOKEN'] = $token;
        }
        $this->post(
            '?r=admin/authentication/sa/login',
            [
                'user' => $user,
                'password' => $password,
                'authMethod' => 'Authdb',
                'login_submit' => 'login',
                'YII_CSRF_TOKEN' => $token ?? '',
            ],
            $host
        );
    }

    public function csrfToken(): ?string
    {
        if (preg_match('/"csrfToken":"([^"]+)"/', $this->body, $m)) {
            return $m[1];
        }
        if (preg_match('/name="YII_CSRF_TOKEN"\s+value="([^"]+)"/', $this->body, $m)) {
            return $m[1];
        }
        if (preg_match('/value="([^"]+)"\s+name="YII_CSRF_TOKEN"/', $this->body, $m)) {
            return $m[1];
        }
        return null;
    }

    public function cookie(string $name): ?string
    {
        return $this->cookies[$name] ?? null;
    }

    public function location(): string
    {
        foreach ($this->headers as $header) {
            if (stripos($header, 'Location:') === 0) {
                return trim(substr($header, 9));
            }
        }
        return '';
    }

    private function send(string $method, string $route, ?array $data, ?string $host, array $extraHeaders = [], bool $json = false): void
    {
        $ch = curl_init(self::BASE . $route);
        $requestHeaders = array_merge(['Host: ' . ($host ?? $this->host)], $extraHeaders);
        if (!empty($this->cookies)) {
            $pairs = [];
            foreach ($this->cookies as $name => $value) {
                $pairs[] = $name . '=' . $value;
            }
            $requestHeaders[] = 'Cookie: ' . implode('; ', $pairs);
        }

        $this->headers = [];
        $this->body = '';
        $this->status = 0;
        $this->transportError = '';

        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_TIMEOUT => 120,
            CURLOPT_CONNECTTIMEOUT => 10,
            CURLOPT_HTTPHEADER => $requestHeaders,
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HEADERFUNCTION => function ($handle, $line) {
                $trimmed = trim($line);
                if ($trimmed === '') {
                    return strlen($line);
                }
                $this->headers[] = $trimmed;
                if (stripos($trimmed, 'Set-Cookie:') === 0) {
                    $cookie = trim(substr($trimmed, 11));
                    $pair = explode(';', $cookie, 2)[0];
                    $eq = strpos($pair, '=');
                    if ($eq !== false) {
                        $name = trim(substr($pair, 0, $eq));
                        $value = substr($pair, $eq + 1);
                        if (preg_match('/max-age\s*=\s*0/i', $cookie) || strcasecmp($value, 'deleted') === 0) {
                            unset($this->cookies[$name]);
                        } else {
                            $this->cookies[$name] = urldecode($value);
                        }
                    }
                }
                return strlen($line);
            },
        ]);

        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, $json ? json_encode($data) : http_build_query($data));
        }

        $result = curl_exec($ch);
        $this->body = is_string($result) ? $result : '';
        $this->status = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        $this->transportError = (string) curl_error($ch);
        curl_close($ch);
    }
}

/**
 * Filesystem mailbox and database helpers.
 */
class Fixtures
{
    public static function resetMail(): void
    {
        foreach (glob(Client::MAIL_DIR . '/*') ?: [] as $file) {
            @unlink($file);
        }
    }

    public static function clearAllowedHosts(): void
    {
        @unlink(Client::ALLOWED_HOSTS_FILE);
    }

    /** @return array<int, array{to:string,subject:string,body:string,raw:string,file:string}> */
    public static function mails(): array
    {
        $mails = [];
        foreach (glob(Client::MAIL_DIR . '/*') ?: [] as $file) {
            $raw = (string) file_get_contents($file);
            $mails[] = self::parseMail($raw, $file);
        }
        usort($mails, fn ($a, $b) => strcmp($a['file'], $b['file']));
        return $mails;
    }

    /** @return array<int, array{to:string,subject:string,body:string,raw:string,file:string}> */
    public static function mailsTo(string $recipient): array
    {
        return array_values(array_filter(
            self::mails(),
            fn ($mail) => stripos($mail['to'], $recipient) !== false
        ));
    }

    private static function parseMail(string $raw, string $file): array
    {
        $separator = "\r\n\r\n";
        $position = strpos($raw, $separator);
        $length = 4;
        if ($position === false) {
            $separator = "\n\n";
            $position = strpos($raw, $separator);
            $length = 2;
        }
        $head = $position === false ? $raw : substr($raw, 0, $position);
        $body = $position === false ? '' : substr($raw, $position + $length);
        $headers = [];
        foreach (preg_split('/\r?\n/', $head) as $line) {
            if (preg_match('/^([^:]+):\s*(.*)$/', $line, $m)) {
                $headers[strtolower(trim($m[1]))] = $m[2];
            }
        }
        return [
            'to' => $headers['to'] ?? '',
            'subject' => $headers['subject'] ?? '',
            'body' => $body,
            'raw' => $raw,
            'file' => $file,
        ];
    }

    /** @return string[] */
    public static function urls(array $mail): array
    {
        preg_match_all('~https?://[^\s"\'<>\)]+~i', $mail['raw'], $m);
        return array_values(array_unique($m[0]));
    }

    /** @return string[] */
    public static function linkHosts(array $mail): array
    {
        $hosts = [];
        foreach (self::urls($mail) as $url) {
            $host = parse_url($url, PHP_URL_HOST);
            if (is_string($host) && $host !== '') {
                $hosts[] = self::normalizeHost($host);
            }
        }
        return array_values(array_unique($hosts));
    }

    public static function normalizeHost(string $host): string
    {
        $host = strtolower(trim($host, " \t\n\r\0\x0B[]"));
        if (!str_contains($host, '::') && ($pos = strrpos($host, ':')) !== false) {
            $host = substr($host, 0, $pos);
        }
        return $host;
    }

    public static function db(): PDO
    {
        return new PDO(
            'mysql:host=127.0.0.1;port=3307;dbname=limesurvey;charset=utf8mb4',
            'limesurvey',
            'lspass',
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );
    }

    public static function clearForgotPasswordState(): void
    {
        self::db()->exec('UPDATE lime_users SET last_forgot_email_password = NULL');
    }

    public static function deleteUserByName(string $name): void
    {
        $db = self::db();
        $stmt = $db->prepare('SELECT uid FROM lime_users WHERE users_name = ?');
        $stmt->execute([$name]);
        $uid = $stmt->fetchColumn();
        if ($uid !== false) {
            $db->prepare('DELETE FROM lime_permissions WHERE uid = ?')->execute([$uid]);
            $db->prepare('DELETE FROM lime_users WHERE uid = ?')->execute([$uid]);
        }
    }

    public static function deleteTokenByEmail(string $email): void
    {
        $db = self::db();
        $stmt = $db->prepare(
            'SELECT COUNT(*) FROM information_schema.tables
             WHERE table_schema = DATABASE() AND table_name = ?'
        );
        $stmt->execute(['lime_tokens_' . Client::SURVEY_ID]);
        if ((int) $stmt->fetchColumn() === 0) {
            return;
        }
        $db->prepare('DELETE FROM lime_tokens_' . Client::SURVEY_ID . ' WHERE email = ?')->execute([$email]);
    }
}
