<?php

/**
 * Shared harness for the hidden suites.
 *
 * Every test drives the running application over HTTP (the product's own endpoints) and
 * inspects the response. The database is only used to look up record identifiers and to
 * compute expectations, never to produce the value under test.
 */
abstract class AppTestCase extends PHPUnit\Framework\TestCase
{
    /** Base URL of the application under test. */
    protected const BASE = 'http://127.0.0.1:8099';

    /** Database port the verifier starts the product's database on. */
    protected static function dbPort(): int
    {
        return (int) (getenv('OSM_DB_PORT') ?: 3307);
    }

    /** @var HttpClient|null */
    private static $admin;
    private static $clerk;

    protected function admin(): HttpClient
    {
        if (!isset(self::$admin)) {
            self::$admin = $this->signIn('admin', 'testpass');
        }

        return self::$admin;
    }

    /**
     * A user who may work with the users-and-permissions area but has no permission on the
     * customer records module (and therefore none on the plugins that belong to it).
     */
    protected function clerk(): HttpClient
    {
        if (!isset(self::$clerk)) {
            self::$clerk = $this->signIn('clerk', 'testpass');
        }

        return self::$clerk;
    }

    protected function signIn(string $username, string $password): HttpClient
    {
        $client = new HttpClient(self::BASE);
        $client->login($username, $password);

        return $client;
    }

    protected static function db(): PDO
    {
        static $pdo;

        if (!isset($pdo)) {
            $pdo = new PDO('mysql:host=127.0.0.1;port='.self::dbPort().';dbname=osm;charset=utf8mb4', 'root', '', [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            ]);
        }

        return $pdo;
    }

    protected static function moduleId(string $name): int
    {
        $stmt = self::db()->prepare('SELECT `id` FROM `zz_modules` WHERE `name` = ? LIMIT 1');
        $stmt->execute([$name]);

        return (int) $stmt->fetchColumn();
    }

    protected static function groupId(string $title): int
    {
        $stmt = self::db()->prepare('SELECT `id_record` FROM `zz_groups_lang` WHERE `id_lang` = 1 AND `title` = ? LIMIT 1');
        $stmt->execute([$title]);

        return (int) $stmt->fetchColumn();
    }

    /** GET a page and require a rendered (2xx) response. */
    protected function fetchPage(HttpClient $client, string $path): string
    {
        [$status, $body] = $client->get($path);
        $this->assertSame(200, $status, 'the page did not render (HTTP '.$status.')');

        return $body;
    }

    /** GET a search endpoint and decode its JSON answer. */
    protected function fetchSelect(HttpClient $client, string $query): array
    {
        [$status, $body] = $client->get('/ajax_select.php?'.$query);
        $this->assertSame(200, $status, 'the search endpoint answered HTTP '.$status);
        $data = json_decode($body, true);
        $this->assertIsArray($data, 'the search endpoint did not answer JSON');

        return $data;
    }

    /** Every display-text value of a select2 answer, children (optgroups) included. */
    protected static function displayTexts(array $data): array
    {
        $out = [];
        $walk = function ($items) use (&$walk, &$out) {
            foreach ($items as $item) {
                if (!is_array($item)) {
                    continue;
                }
                if (isset($item['children']) && is_array($item['children'])) {
                    $walk($item['children']);
                    continue;
                }
                if (array_key_exists('text', $item)) {
                    $out[] = (string) $item['text'];
                }
            }
        };
        $walk($data['results'] ?? []);

        return $out;
    }

    /** The slice of HTML that carries one card header. */
    protected static function cardHeader(string $html, string $label): string
    {
        $start = strpos($html, $label);
        if ($start === false) {
            return '';
        }
        $end = strpos($html, '</h3>', $start);

        return substr($html, $start, ($end === false ? $start + 2000 : $end) - $start);
    }
}
