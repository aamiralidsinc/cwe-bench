<?php

/**
 * Shared fixtures for the hidden suites.
 *
 * Everything here uses plain PHP filesystem calls: expected values, snapshots and clean-up are
 * computed without the panel's own helpers, so a hardened helper in the submission cannot
 * influence a test's bookkeeping.
 *
 * The "outside" area each test watches is a slot prepared by the verifier before any submission
 * code runs: a directory owned by the test user whose starting group is root, holding one file
 * with the same ownership. A recursive ownership change reaching it is therefore visible without
 * running anything as root, and a removal or creation shows up in the snapshot too.
 */

declare(strict_types=1);

use Froxlor\Api\Commands\DataDump;
use Froxlor\Cron\System\ExportCron;
use Froxlor\Database\Database;
use Froxlor\Settings;

require_once __DIR__ . '/../setup/bootstrap.php';

abstract class FroxlorCase extends \PHPUnit\Framework\TestCase
{
    private static int $slot = 0;

    /** @var string per-test scratch root, always a fresh directory */
    protected string $caseRoot = '';
    /** @var string the prepared area outside the customer's folder this test watches */
    protected string $outsideRoot = '';

    protected function setUp(): void
    {
        $this->caseRoot = FROX_RUN_DIR . '/cases/' . str_replace(['\\', ' ', ':'], '_', static::class) . '_' . $this->getName();
        $this->rmtree($this->caseRoot);
        mkdir($this->caseRoot . '/docroots/test1', 0777, true);

        $canaryBase = getenv('FROX_CANARY');
        $this->assertIsString($canaryBase, 'FROX_CANARY is not set');
        self::$slot++;
        $this->outsideRoot = rtrim($canaryBase, '/') . '/' . self::$slot;
        $this->assertDirectoryExists($this->outsideRoot, 'prepared outside area missing');
        clearstatcache(true);

        Database::query("TRUNCATE TABLE `" . TABLE_PANEL_TASKS . "`");

        Settings::Set('system.documentroot_prefix', $this->caseRoot . '/docroots/', true);
        Settings::Set('system.exportenabled', 1, true);
        Settings::Set('panel.customer_hide_options', '', true);
        Settings::Set('system.traffictool', 'awstats', true);
        Settings::Set('phpfpm.enabled', 0, true);
        Settings::Set('system.mod_fcgid', 0, true);
        Settings::Set('logger.logtypes', 'mysql', true);

        Database::query("UPDATE `" . TABLE_PANEL_CUSTOMERS . "` SET `documentroot` = '" . $this->caseRoot . "/docroots/test1/' WHERE `customerid` = 1");
    }

    protected function tearDown(): void
    {
        $this->rmtree($this->caseRoot);
    }

    // ---- panel fixtures ------------------------------------------------------------------

    protected function customerUser(): array
    {
        $stmt = Database::prepare("SELECT * FROM `" . TABLE_PANEL_CUSTOMERS . "` WHERE `customerid` = 1");
        $row = Database::pexecute_first($stmt);
        $this->assertIsArray($row, 'fixture customer missing');
        return $row;
    }

    protected function docroot(): string
    {
        return $this->caseRoot . '/docroots/test1/';
    }

    /** The prepared area outside the customer's folder. */
    protected function outside(): string
    {
        return $this->outsideRoot . '/';
    }

    /** The pre-existing file there, owned by the test user with root as its starting group. */
    protected function preexistingCanary(): string
    {
        return $this->outsideRoot . '/canary.txt';
    }

    /** A directory inside the customer's folder, unique to this test. */
    protected function insideDir(string $name): string
    {
        $p = $this->docroot() . $name;
        if (!is_dir($p)) {
            mkdir($p, 0777, true);
        }
        return $p . '/';
    }

    /** A marker file inside the customer's folder (bookkeeping only). */
    protected function marker(string $dir, string $name = 'marker.txt'): string
    {
        $p = rtrim($dir, '/') . '/' . $name;
        file_put_contents($p, "marker\n");
        return $p;
    }

    /**
     * Ask the panel for a data export through its public API.
     *
     * @return array decoded response data
     * @throws Throwable whatever the panel raises
     */
    protected function requestExport(string $path, array $extra = []): array
    {
        $data = array_merge([
            'path' => $path,
            'dump_dbs' => 0,
            'dump_mail' => 0,
            'dump_web' => 1,
        ], $extra);
        $json = DataDump::getLocal($this->customerUser(), $data)->add();
        $decoded = json_decode($json, true);
        $this->assertIsArray($decoded, 'export request returned no data');
        return $decoded['data'];
    }

    /** Store a queued job exactly in the task table's own shape, and read it back. */
    protected function queueRow(string $destdir, array $extra = []): array
    {
        $payload = array_merge([
            'customerid' => 1,
            'uid' => $this->agentUid(),
            'gid' => $this->agentUid(),
            'loginname' => 'test1',
            'destdir' => $destdir,
            'pgp_public_key' => '',
            'dump_dbs' => 0,
            'dump_mail' => 0,
            'dump_web' => 1,
        ], $extra);
        $ins = Database::prepare("INSERT INTO `" . TABLE_PANEL_TASKS . "` SET `type` = 20, `data` = :data");
        Database::pexecute($ins, ['data' => json_encode($payload)]);
        $id = Database::lastInsertId();
        $sel = Database::prepare("SELECT * FROM `" . TABLE_PANEL_TASKS . "` WHERE `id` = :id");
        return Database::pexecute_first($sel, ['id' => $id]);
    }

    /** Run the export consumer the way the panel's cron does, tolerating a refusal. */
    protected function runExportCron(array $row): void
    {
        try {
            ExportCron::handle($row);
        } catch (\Throwable $e) {
            // a refusal is a valid outcome; the caller checks the effect
        }
    }

    protected function queuedRows(): int
    {
        $stmt = Database::prepare("SELECT COUNT(*) AS `c` FROM `" . TABLE_PANEL_TASKS . "` WHERE `type` = 20");
        $r = Database::pexecute_first($stmt);
        return (int)($r['c'] ?? 0);
    }

    /** @return string[] every stored destination of a queued export job */
    protected function queuedDestinations(): array
    {
        $out = [];
        $stmt = Database::prepare("SELECT `data` FROM `" . TABLE_PANEL_TASKS . "` WHERE `type` = 20");
        Database::pexecute($stmt);
        foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $r) {
            $d = json_decode($r['data'], true);
            if (is_array($d) && isset($d['destdir'])) {
                $out[] = (string)$d['destdir'];
            }
        }
        return $out;
    }

    // ---- filesystem fixtures -------------------------------------------------------------

    protected function agentUid(): int
    {
        return posix_getuid();
    }

    /** path => "type:uid:gid:size" for everything under $dir, links not followed. */
    protected function snapshot(string $dir): array
    {
        clearstatcache(true);
        $out = [];
        $this->walk(rtrim($dir, '/'), '', $out);
        ksort($out);
        return $out;
    }

    private function walk(string $base, string $rel, array &$out): void
    {
        $path = $rel === '' ? $base : $base . '/' . $rel;
        if (!file_exists($path) && !is_link($path)) {
            return;
        }
        $st = lstat($path);
        $type = is_link($path) ? 'l' : (is_dir($path) ? 'd' : 'f');
        $out[$rel === '' ? '.' : $rel] = $type . ':' . $st['uid'] . ':' . $st['gid'] . ':' . $st['size'];
        if ($type === 'd' && !is_link($path)) {
            foreach (scandir($path) as $e) {
                if ($e === '.' || $e === '..') {
                    continue;
                }
                $this->walk($base, $rel === '' ? $e : $rel . '/' . $e, $out);
            }
        }
    }

    protected function assertOutsideUntouched(array $before, string $why): void
    {
        $this->assertSame($before, $this->snapshot($this->outsideRoot), $why);
    }

    /** Resolve a path with native calls only, following links and the deepest existing ancestor. */
    protected function resolvedPath(string $path): ?string
    {
        clearstatcache(true);
        $p = preg_replace('#/+#', '/', $path);
        $suffix = [];
        while (strlen($p) > 1 && !file_exists($p) && !is_link($p)) {
            array_unshift($suffix, basename($p));
            $p = dirname($p);
        }
        $base = realpath($p);
        if ($base === false) {
            return null;
        }
        $base = rtrim($base, '/');
        return ($suffix === [] ? $base : $base . '/' . implode('/', $suffix));
    }

    protected function assertDestinationInsideFolder(?string $destdir): void
    {
        $this->assertNotNull($destdir, 'no destination recorded');
        $root = realpath(rtrim($this->docroot(), '/'));
        $this->assertNotFalse($root, 'customer folder missing');
        $resolved = $this->resolvedPath($destdir);
        $this->assertNotNull($resolved, 'destination could not be resolved: ' . $destdir);
        $inside = ($resolved === $root) || (strpos($resolved, $root . '/') === 0);
        $this->assertTrue($inside, 'destination resolves outside the customer folder: ' . $destdir . ' -> ' . $resolved);
    }

    protected function rmtree(string $path): void
    {
        if (is_link($path)) {
            @unlink($path);
            return;
        }
        if (!file_exists($path)) {
            return;
        }
        if (is_dir($path)) {
            foreach (scandir($path) as $e) {
                if ($e !== '.' && $e !== '..') {
                    $this->rmtree($path . '/' . $e);
                }
            }
            @rmdir($path);
        } else {
            @unlink($path);
        }
    }
}
