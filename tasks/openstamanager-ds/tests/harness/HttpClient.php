<?php

/**
 * Minimal HTTP client for the running application: one cookie jar per instance, so each
 * test session is independent (the product keeps one active session per user).
 */
final class HttpClient
{
    private string $base;
    private string $jar;

    public function __construct(string $base)
    {
        $this->base = rtrim($base, '/');
        $this->jar = tempnam(sys_get_temp_dir(), 'osmjar');
        register_shutdown_function(function () {
            @unlink($this->jar);
        });
    }

    public function login(string $username, string $password): void
    {
        [$status, , $location] = $this->request('/index.php', true, http_build_query([
            'op' => 'login',
            'username' => $username,
            'password' => $password,
        ]));

        if ($status !== 302 || !str_contains((string) $location, 'controller.php')) {
            throw new RuntimeException("login for '{$username}' was refused (HTTP {$status})");
        }
    }

    /** @return array{0:int,1:string} */
    public function get(string $path): array
    {
        [$status, $body] = $this->request($path, false);

        return [$status, $body];
    }

    /** @return array{0:int,1:string,2:?string} */
    private function request(string $path, bool $post, ?string $fields = null): array
    {
        $ch = curl_init($this->base.$path);
        $options = [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_COOKIEFILE => $this->jar,
            CURLOPT_COOKIEJAR => $this->jar,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_TIMEOUT => 60,
            CURLOPT_HTTPHEADER => ['Accept: text/html,application/json'],
        ];
        if ($post) {
            $options[CURLOPT_POST] = true;
            $options[CURLOPT_POSTFIELDS] = (string) $fields;
        }
        $headers = [];
        $options[CURLOPT_HEADERFUNCTION] = function ($ch, $line) use (&$headers) {
            $headers[] = trim($line);

            return strlen($line);
        };
        curl_setopt_array($ch, $options);
        $body = curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $location = null;
        foreach ($headers as $header) {
            if (stripos($header, 'location:') === 0) {
                $location = trim(substr($header, 9));
            }
        }
        curl_close($ch);

        if ($body === false) {
            throw new RuntimeException('request to '.$path.' failed');
        }

        return [$status, (string) $body, $location];
    }
}
