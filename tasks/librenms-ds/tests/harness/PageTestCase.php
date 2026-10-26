<?php

namespace Bench;

use App\Models\Device;
use App\Models\User;
use Illuminate\Foundation\Testing\Concerns\InteractsWithDatabase;
use Illuminate\Foundation\Testing\TestCase as LaravelTestCase;
use Illuminate\Support\Facades\DB;
use Spatie\Permission\Models\Role;

/**
 * Base class for the behavioural suites. Every test boots the real application, migrates the
 * project's in-memory SQLite schema, seeds device data and drives a real HTTP route (or the
 * real legacy ajax script) as an authenticated administrator.
 */
abstract class PageTestCase extends LaravelTestCase
{
    use InteractsWithDatabase;

    protected string $connection = 'testing_memory';
    protected Device $device;
    protected User $admin;
    private string $benchRoot = '';

    /**
     * Boot the application with its writable directories under /tmp. The verifier restores a
     * /workspace whose ownership does not necessarily match the unprivileged test user, and the
     * framework refuses to boot when bootstrap/cache or storage is not writable.
     */
    public function createApplication()
    {
        $root = '/tmp/librenms-bench-' . getmypid() . '-' . bin2hex(random_bytes(6));
        foreach (['cache', 'storage/framework/views', 'storage/framework/cache',
                  'storage/framework/sessions', 'storage/logs', 'logs'] as $dir) {
            @mkdir($root . '/' . $dir, 0777, true);
        }
        $this->benchRoot = $root;

        $app = require \Illuminate\Foundation\Application::inferBasePath() . '/bootstrap/app.php';
        $app->useBootstrapPath($root);
        $app->useStoragePath($root . '/storage');
        $app->make(\Illuminate\Contracts\Console\Kernel::class)->bootstrap();

        return $app;
    }

    protected function setUp(): void
    {
        parent::setUp();

        // Legacy page templates read many optional array keys; keep those notices out of the
        // request so a page render reflects behaviour, not PHP 8 warning conversion.
        error_reporting(E_ALL & ~E_WARNING & ~E_NOTICE & ~E_DEPRECATED);

        $this->artisan('migrate:fresh', ['--database' => $this->connection]);
        $current = config('database.default');
        config(['database.default' => $this->connection]);
        DB::purge($current);

        $this->admin = User::factory()->create(['enabled' => 1, 'username' => 'benchadmin']);
        $this->admin->assignRole(Role::findOrCreate('admin'));

        $this->device = Device::factory()->create([
            'hostname' => 'benchhost',
            'os' => 'linux',
            'type' => 'server',
            'hardware' => 'bench-hw',
            'status' => 1,
            'disabled' => 0,
        ]);
    }

    protected function tearDown(): void
    {
        $this->beforeApplicationDestroyed(function (): void {
            $this->getConnection()->disconnect();
            if ($this->benchRoot !== '') {
                @exec('rm -rf ' . escapeshellarg($this->benchRoot));
            }
        });

        parent::tearDown();
    }

    protected function deviceId(): int
    {
        return (int) $this->device->device_id;
    }

    /* ------------------------------------------------------------------ HTTP */

    protected function fetchPage(string $path): string
    {
        $response = $this->actingAs($this->admin)->get($path);
        $status = $response->getStatusCode();
        $this->assertSame(200, $status, "GET $path did not render (status $status)");

        return $response->getContent();
    }

    /** The alerts bootgrid endpoint: the real script the alerts page calls. */
    protected function fetchAlertsTable(): array
    {
        $previousRequest = $_REQUEST;
        $previousGet = $_GET;

        $this->actingAs($this->admin);
        $_REQUEST = ['id' => 'alerts', 'current' => 1, 'rowCount' => 50, 'searchPhrase' => '', 'sort' => []];
        $_GET = $_REQUEST;

        ob_start();
        try {
            require '/workspace/html/ajax_table.php';
        } finally {
            $output = ob_get_clean();
            $_REQUEST = $previousRequest;
            $_GET = $previousGet;
        }

        $decoded = json_decode($output, true);
        $this->assertIsArray($decoded, 'alerts endpoint returned no JSON: ' . substr($output, 0, 400));

        return $decoded['rows'] ?? [];
    }

    /** Return the rendered alert-details cell that contains $marker. */
    protected function alertDetailsCell(string $marker): string
    {
        $rows = $this->fetchAlertsTable();
        $this->assertNotEmpty($rows, 'alerts endpoint returned no rows');

        foreach ($rows as $row) {
            foreach ($row as $value) {
                if (is_string($value) && str_contains($value, $marker)) {
                    return $value;
                }
            }
        }

        $this->fail("the recorded value $marker was not shown at all");
    }

    /* ------------------------------------------------------------- DOM views */

    protected function xpath(string $html): \DOMXPath
    {
        $document = new \DOMDocument();
        $previous = libxml_use_internal_errors(true);
        $document->loadHTML('<?xml encoding="utf-8">' . $html);
        libxml_clear_errors();
        libxml_use_internal_errors($previous);

        return new \DOMXPath($document);
    }

    /**
     * The value must be displayed, but must not have become an element, an attribute or
     * executable script. Checked on the DOM the browser would build (entities decoded).
     */
    protected function assertPayloadInert(string $html, string $marker): void
    {
        $xpath = $this->xpath($html);
        $hits = [];

        foreach ($xpath->query('//*[@src="x"]') as $element) {
            $hits[] = 'created element <' . $element->nodeName . '>';
        }

        foreach ($xpath->query('//*[@onerror]') as $element) {
            if (str_contains($element->getAttribute('onerror'), $marker)) {
                $hits[] = 'onerror handler on <' . $element->nodeName . '>';
            }
        }

        foreach ($xpath->query('//@*') as $attribute) {
            if (str_starts_with($attribute->nodeName, 'on')
                && (str_contains($attribute->value, $marker) || str_contains($attribute->value, '<img src=x'))) {
                $hits[] = 'payload markup inside attribute ' . $attribute->nodeName;
            }
        }

        foreach ($xpath->query('//script') as $script) {
            if (str_contains($script->textContent, $marker)) {
                $hits[] = 'script element carrying the payload';
            }
        }

        $this->assertSame([], array_values(array_unique($hits)),
            'a device-supplied value became markup or code: ' . implode('; ', $hits));
        $this->assertStringContainsString('Zq7x', $html,
            'the recorded value vanished instead of being shown as text');
    }

    /**
     * A value placed inside an inline event handler must not terminate the surrounding
     * JavaScript string. $marker is the identifier after the quote.
     */
    protected function assertQuoteInert(string $html, string $marker): void
    {
        $xpath = $this->xpath($html);
        $hits = [];

        foreach ($xpath->query('//@*') as $attribute) {
            if (! str_starts_with($attribute->nodeName, 'on')) {
                continue;
            }
            if (preg_match("/(?<!\\\\)'\\);\\s*window\\." . preg_quote($marker, '/') . '/', $attribute->value)) {
                $hits[] = 'attribute ' . $attribute->nodeName;
            }
        }

        $this->assertSame([], $hits, 'a quote in a device value closed an inline script string');
        $this->assertStringContainsString('Zq7q', $html,
            'the recorded value vanished instead of being shown as text');
    }

    /* ----------------------------------------------------------- payloads */

    /** An element payload with a visible prefix and a unique marker. */
    protected function htmlPayload(string $marker): string
    {
        return 'Zq7x <img src=x onerror=window.' . $marker . '=1>';
    }

    /** A payload that terminates a single-quoted JavaScript string. */
    protected function quotePayload(string $marker): string
    {
        return "Zq7q');window." . $marker . '=1;//';
    }

    /* ------------------------------------------------------------ seed data */

    protected function seedPort(array $overrides = []): int
    {
        $row = array_merge([
            'device_id' => $this->deviceId(),
            'ifIndex' => 5,
            'ifName' => 'eth0',
            'ifDescr' => 'eth0',
            'ifAlias' => '',
            'ifSpeed' => 1000000,
            'ifAdminStatus' => 'up',
            'ifOperStatus' => 'up',
            'ifType' => 'ethernetCsmacd',
            'ifMtu' => 1500,
            'poll_time' => time(),
            'poll_prev' => time(),
            'ifLastChange' => time(),
        ], $overrides);

        DB::table('ports')->insert($row);

        return (int) DB::table('ports')
            ->where('device_id', $row['device_id'])
            ->where('ifIndex', $row['ifIndex'])
            ->value('port_id');
    }

    protected function seedStorage(array $overrides = []): void
    {
        DB::table('storage')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'type' => 'ext4',
            'storage_index' => '1',
            'storage_type' => 'ext4',
            'storage_descr' => 'data',
            'storage_size' => 1000000,
            'storage_units' => 1024,
            'storage_used' => 100,
            'storage_free' => 900,
            'storage_perc' => 10,
            'storage_perc_warn' => 90,
        ], $overrides));
    }

    protected function seedSensor(array $overrides = []): void
    {
        DB::table('sensors')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'sensor_class' => 'temperature',
            'sensor_index' => '1',
            'sensor_type' => 'temperature',
            'sensor_descr' => 'cpu temp',
            'sensor_current' => 20,
            'sensor_limit' => 80,
            'sensor_limit_low' => 0,
            'sensor_alert' => 1,
            'sensor_oid' => '.1.3.6.1.4.1.9.1',
            'poller_type' => 'snmp',
        ], $overrides));
    }

    protected function seedMempool(array $overrides = []): void
    {
        DB::table('mempools')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'mempool_index' => '1',
            'mempool_type' => 'hitachi',
            'mempool_class' => 'system',
            'mempool_descr' => 'system memory',
            'mempool_perc' => 10,
            'mempool_used' => 100,
            'mempool_free' => 900,
            'mempool_total' => 1000,
        ], $overrides));
    }

    protected function seedProcessor(array $overrides = []): void
    {
        DB::table('processors')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'processor_oid' => '.1.3.6.1.4.1.9.2',
            'processor_index' => '1',
            'processor_type' => 'cpu',
            'processor_descr' => 'CPU 0',
            'processor_usage' => 5,
        ], $overrides));
    }

    protected function seedVlan(array $overrides = []): void
    {
        DB::table('vlans')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'vlan_vlan' => 10,
            'vlan_domain' => 1,
            'vlan_name' => 'users',
            'vlan_type' => 'ethernet',
            'vlan_state' => 'active',
        ], $overrides));
    }

    protected function seedPortVlan(int $portId, array $overrides = []): void
    {
        DB::table('ports_vlans')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'port_id' => $portId,
            'vlan' => 10,
            'baseport' => $portId,
            'cost' => 1,
            'priority' => 1,
            'state' => 'forwarding',
            'untagged' => 0,
        ], $overrides));
    }

    protected function seedBgpPeer(array $overrides = []): void
    {
        DB::table('bgpPeers')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'bgpPeerIdentifier' => '10.1.1.1',
            'bgpPeerRemoteAs' => 65001,
            'bgpPeerDescr' => 'peer',
            'bgpPeerState' => 'established',
            'bgpPeerAdminStatus' => 'start',
            'bgpPeerLastErrorText' => '',
            'bgpPeerLastErrorCode' => 0,
            'bgpPeerLastErrorSubCode' => 0,
            'bgpPeerFsmEstablishedTime' => 10,
            'bgpPeerInUpdateElapsedTime' => 10,
            'bgpPeerInUpdates' => 1,
            'bgpPeerOutUpdates' => 1,
            'bgpPeerInTotalMessages' => 1,
            'bgpPeerOutTotalMessages' => 1,
            'bgpLocalAddr' => '10.1.1.2',
            'bgpPeerRemoteAddr' => '10.1.1.1',
            'astext' => '65001',
        ], $overrides));
    }

    protected function seedVrf(array $overrides = []): void
    {
        DB::table('vrfs')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'vrf_oid' => '99',
            'vrf_name' => 'red',
            'mplsVpnVrfDescription' => 'red vrf',
            'mplsVpnVrfRouteDistinguisher' => '65001:99',
        ], $overrides));
    }

    protected function seedSla(array $overrides = []): int
    {
        DB::table('slas')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'sla_nr' => 1,
            'tag' => 'office',
            'owner' => 'ops',
            'rtt_type' => 'icmp',
            'status' => 1,
            'deleted' => 0,
            'opstatus' => 0,
        ], $overrides));

        return (int) DB::table('slas')->where('device_id', $this->deviceId())->max('sla_id');
    }

    protected function seedProcess(array $overrides = []): void
    {
        DB::table('processes')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'pid' => 1,
            'vsz' => 1,
            'rss' => 1,
            'cputime' => '0:01',
            'user' => 'root',
            'command' => '/sbin/init',
        ], $overrides));
    }

    protected function seedHrDevice(array $overrides = []): void
    {
        DB::table('hrDevice')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'hrDeviceIndex' => 1,
            'hrDeviceDescr' => 'GenuineIntel',
            'hrDeviceType' => 'hrDeviceProcessor',
            'hrDeviceStatus' => 1,
            'hrDeviceErrors' => 0,
            'hrProcessorLoad' => 1,
        ], $overrides));
    }

    protected function seedWirelessSensor(array $overrides = []): void
    {
        DB::table('wireless_sensors')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'sensor_class' => 'rssi',
            'sensor_index' => 1,
            'sensor_type' => 'rssi',
            'sensor_descr' => 'station',
            'sensor_current' => 20,
            'sensor_limit' => 30,
            'sensor_limit_low' => 0,
            'sensor_alert' => 1,
            'sensor_deleted' => 0,
            'sensor_oids' => '.1.3.6.1.4.1.9.3',
        ], $overrides));
    }

    protected function seedDiskio(array $overrides = []): void
    {
        DB::table('ucd_diskio')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'diskio_index' => 1,
            'diskio_descr' => 'sda',
        ], $overrides));
    }

    protected function seedMpls(array $overrides = []): void
    {
        $this->seedVrf();
        DB::table('mpls_lsps')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'vrf_oid' => '99',
            'lsp_oid' => '1',
            'mplsLspRowStatus' => 'active',
            'mplsLspName' => 'lsp-one',
            'mplsLspAdminState' => 'inService',
            'mplsLspOperState' => 'inService',
            'mplsLspFromAddr' => '10.9.9.8',
            'mplsLspToAddr' => '10.9.9.9',
            'mplsLspAge' => 100,
            'mplsLspPrimaryTimeUp' => 100,
            'mplsLspTransitions' => 1,
            'mplsLspLastChange' => time(),
            'mplsLspLastTransition' => time(),
            'mplsLspConfiguredPaths' => 1,
            'mplsLspStandbyPaths' => 0,
            'mplsLspOperationalPaths' => 1,
            'mplsLspType' => 'static',
            'mplsLspFastReroute' => 'false',
        ], $overrides));
    }

    protected function seedIsis(array $overrides = []): void
    {
        DB::table('isis_adjacencies')->insert(array_merge([
            'device_id' => $this->deviceId(),
            'ifIndex' => 5,
            'isisISAdjState' => 'up',
            'isisISAdjNeighSysType' => 'L1',
            'isisISAdjNeighSysID' => '0000.0000.0001',
            'isisISAdjAreaAddress' => '49.0001',
            'isisISAdjIPAddrAddress' => '10.0.0.1',
            'isisCircAdminState' => 'on',
            'isisISAdjLastUpTime' => 1,
        ], $overrides));
    }

    protected function seedAlert(array $detailRows): void
    {
        $ruleId = DB::table('alert_rules')->insertGetId([
            'name' => 'bench rule',
            'severity' => 'critical',
            'query' => 'SELECT 1',
            'builder' => '{}',
            'extra' => '',
            'disabled' => 0,
        ]);

        DB::table('alerts')->insert([
            'device_id' => $this->deviceId(),
            'rule_id' => $ruleId,
            'state' => 1,
            'alerted' => 1,
            'open' => 1,
            'timestamp' => date('Y-m-d H:i:s'),
            'info' => '{}',
        ]);

        DB::table('alert_log')->insert([
            'rule_id' => $ruleId,
            'device_id' => $this->deviceId(),
            'time_logged' => date('Y-m-d H:i:s'),
            'state' => 1,
            'details' => gzcompress(json_encode(['rule' => $detailRows])),
        ]);
    }
}
