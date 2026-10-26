<?php
/**
 * Shared harness for the hidden Dolibarr API suites.
 *
 * Everything here talks to the running application over HTTP (the real entry point) and to a
 * private database only to create and inspect fixtures. No assertion depends on product code
 * beyond the HTTP responses and the stored rows.
 */

abstract class ApiTestCase extends \PHPUnit\Framework\TestCase
{
    protected const DB_HOST = '127.0.0.1';
    protected const DB_PORT = 3307;
    protected const DB_NAME = 'dolibarr';
    protected const DB_USER = 'doli';
    protected const DB_PASS = 'dolipass';

    protected const API = 'http://127.0.0.1:8080/api/index.php';

    // Seeded actors. See tests/setup/seed.sql.
    protected const KEY_ADMIN = 'admin_key';
    protected const KEY_MANAGER = 'mgr_key';       // id 2, parent 1
    protected const KEY_SUB = 'sub_key';           // id 3, parent 2 (manager's report)
    protected const KEY_OUT = 'out_key';           // id 4, parent 1 (outside manager's hierarchy)
    protected const KEY_VAL = 'val_key';           // id 5, parent 1
    protected const KEY_ALL = 'all_key';           // id 6, all-user read permissions
    protected const KEY_WRITER = 'wri_key';        // id 7, all-user write permissions

    protected const UID_ADMIN = 1;
    protected const UID_MANAGER = 2;
    protected const UID_SUB = 3;
    protected const UID_OUT = 4;
    protected const UID_VAL = 5;
    protected const UID_ALL = 6;
    protected const UID_WRITER = 7;

    /** @var mysqli */
    protected static $db;

    public static function setUpBeforeClass(): void
    {
        try {
            self::$db = @new mysqli(self::DB_HOST, self::DB_USER, self::DB_PASS, self::DB_NAME, self::DB_PORT);
        } catch (\Throwable $e) {
            throw new RuntimeException('cannot reach the fixture database: '.$e->getMessage());
        }
        if (!self::$db || self::$db->connect_errno) {
            throw new RuntimeException('cannot reach the fixture database: '.(self::$db ? self::$db->connect_error : 'no handle'));
        }
        self::$db->set_charset('utf8mb4');
    }

    protected function setUp(): void
    {
        $this->cleanFixtures();
    }

    protected function tearDown(): void
    {
        $this->cleanFixtures();
    }

    // ---------------------------------------------------------------- fixtures

    protected static function sqlv($v): string
    {
        if ($v === null) {
            return 'NULL';
        }
        if (is_int($v) || is_float($v)) {
            return (string) $v;
        }
        return "'".self::$db->real_escape_string((string) $v)."'";
    }

    protected function insertRow(string $table, array $row): int
    {
        $cols = array();
        $vals = array();
        foreach ($row as $c => $v) {
            $cols[] = $c;
            $vals[] = self::sqlv($v);
        }
        $sql = 'INSERT INTO '.$table.' ('.implode(',', $cols).') VALUES ('.implode(',', $vals).')';
        if (!self::$db->query($sql)) {
            throw new RuntimeException('fixture insert failed: '.self::$db->error.' :: '.$sql);
        }
        return (int) self::$db->insert_id;
    }

    protected function mkLeave(array $over = array()): int
    {
        $row = array_merge(array(
            'ref' => 'CWETEST-L-'.bin2hex(random_bytes(6)),
            'entity' => 1,
            'fk_user' => self::UID_OUT,
            'fk_user_create' => self::UID_OUT,
            'fk_type' => 3,
            'date_create' => date('Y-m-d H:i:s'),
            'description' => 'cwe fixture leave',
            'date_debut' => date('Y-m-d', strtotime('+20 days')),
            'date_fin' => date('Y-m-d', strtotime('+21 days')),
            'halfday' => 0,
            'nb_open_day' => 2,
            'statut' => 1,
            'fk_validator' => self::UID_ADMIN,
        ), $over);
        return $this->insertRow('llx_holiday', $row);
    }

    protected function mkExpense(array $over = array()): int
    {
        $row = array_merge(array(
            'ref' => 'CWETEST-E-'.bin2hex(random_bytes(6)),
            'entity' => 1,
            'total_ht' => 10,
            'total_tva' => 0,
            'total_ttc' => 10,
            'date_debut' => date('Y-m-d', strtotime('-10 days')),
            'date_fin' => date('Y-m-d', strtotime('-9 days')),
            'date_create' => date('Y-m-d H:i:s'),
            'fk_user_author' => self::UID_OUT,
            'fk_user_creat' => self::UID_OUT,
            'fk_statut' => 0,
            'paid' => 0,
            'note_public' => 'cwe fixture report',
        ), $over);
        return $this->insertRow('llx_expensereport', $row);
    }

    protected function mkLine(int $reportId, array $over = array()): int
    {
        $row = array_merge(array(
            'fk_expensereport' => $reportId,
            'docnumber' => 'CWETEST-D-'.bin2hex(random_bytes(4)),
            'fk_c_type_fees' => 2,
            'comments' => 'cwe fixture line',
            'qty' => 1,
            'subprice' => 10,
            'value_unit' => 10,
            'total_ht' => 10,
            'total_tva' => 0,
            'total_ttc' => 10,
            'date' => date('Y-m-d', strtotime('-10 days')),
        ), $over);
        return $this->insertRow('llx_expensereport_det', $row);
    }

    protected function cleanFixtures(): void
    {
        self::$db->query("DELETE FROM llx_holiday WHERE ref LIKE 'CWETEST-%'");
        self::$db->query("DELETE FROM llx_expensereport_det WHERE fk_expensereport IN (SELECT rowid FROM llx_expensereport WHERE ref LIKE 'CWETEST-%')");
        self::$db->query("DELETE FROM llx_expensereport WHERE ref LIKE 'CWETEST-%'");
        // rows a submission may have created through the API during an attack test
        self::$db->query("DELETE FROM llx_holiday WHERE description LIKE 'cwe-created-%'");
        self::$db->query("DELETE FROM llx_expensereport WHERE note_public LIKE 'cwe-created-%'");
        // rows this suite created through the API during a legitimate-use test
        self::$db->query("DELETE FROM llx_holiday WHERE description LIKE 'cwe-legit-%'");
        self::$db->query("DELETE FROM llx_expensereport WHERE note_public LIKE 'cwe-legit-%'");
    }

    /** @return array<string,mixed>|null */
    protected function row(string $table, int $id): ?array
    {
        $res = self::$db->query('SELECT * FROM '.$table.' WHERE rowid = '.((int) $id));
        if (!$res) {
            throw new RuntimeException('fixture read failed: '.self::$db->error);
        }
        $row = $res->fetch_assoc();
        return $row === null ? null : $row;
    }

    protected function countRows(string $sql): int
    {
        $res = self::$db->query($sql);
        if (!$res) {
            throw new RuntimeException('fixture count failed: '.self::$db->error);
        }
        $row = $res->fetch_row();
        return (int) ($row[0] ?? 0);
    }

    // ---------------------------------------------------------------- HTTP

    /**
     * @return array{status:int,body:string,json:mixed}
     */
    protected function api(string $method, string $path, string $key, ?array $body = null): array
    {
        $url = self::API.$path;
        $payload = $body === null ? null : json_encode($body);
        $last = null;
        for ($attempt = 0; $attempt < 2; $attempt++) {
            $ch = curl_init($url);
            $headers = array('DOLAPIKEY: '.$key, 'Accept: application/json');
            if ($payload !== null) {
                $headers[] = 'Content-Type: application/json';
            }
            curl_setopt_array($ch, array(
                CURLOPT_CUSTOMREQUEST => $method,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_HTTPHEADER => $headers,
                CURLOPT_CONNECTTIMEOUT => 10,
                CURLOPT_TIMEOUT => 60,
            ));
            if ($payload !== null) {
                curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
            }
            $out = curl_exec($ch);
            $status = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
            $err = curl_error($ch);
            curl_close($ch);
            if ($out === false || $status === 0) {
                $last = array('status' => 0, 'body' => (string) $err, 'json' => null);
                usleep(300000);
                continue;
            }
            return array('status' => $status, 'body' => (string) $out, 'json' => json_decode((string) $out, true));
        }
        return $last;
    }

    /** The attack must be refused by the application, not by a server crash. */
    protected function assertBlocked(array $r, string $what = ''): void
    {
        $this->assertNotSame(0, $r['status'], 'no HTTP response for '.$what.': '.substr($r['body'], 0, 300));
        $this->assertGreaterThanOrEqual(400, $r['status'], 'expected a client error for '.$what
            .'; got '.$r['status'].': '.substr($r['body'], 0, 400));
        $this->assertLessThan(500, $r['status'], 'expected a clean client error for '.$what
            .', not a server error; got '.$r['status'].': '.substr($r['body'], 0, 400));
    }

    protected function assertAllowed(array $r, string $what = ''): void
    {
        $this->assertSame(200, $r['status'], 'expected success for '.$what
            .'; got '.$r['status'].': '.substr($r['body'], 0, 400));
    }

    protected function assertBodyHas(array $r, string $needle, string $what = ''): void
    {
        $this->assertStringContainsString($needle, $r['body'], 'expected '.$what.' in the response: '.substr($r['body'], 0, 500));
    }

    protected function assertBodyLacks(array $r, string $needle, string $what = ''): void
    {
        $this->assertStringNotContainsString($needle, $r['body'], 'did not expect '.$what.' in the response: '.substr($r['body'], 0, 500));
    }

    /** Accept either a refusal or a success whose body does not carry the protected marker. */
    protected function assertNotDisclosed(array $r, string $marker, string $what = ''): void
    {
        if ($r['status'] >= 400) {
            $this->assertBlocked($r, $what);
            return;
        }
        $this->assertSame(200, $r['status'], 'unexpected status for '.$what.': '.$r['status']);
        $this->assertBodyLacks($r, $marker, $what);
    }
}
