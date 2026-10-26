<?php

namespace Bench;

use App\Facades\LibrenmsConfig;
use Illuminate\Support\Facades\DB;

/** Recent syslog is shown on the device overview; the fields come from the device. */
class SyslogSecurityTest extends PageTestCase
{
    public function testSyslogProgramAndMessageAreInert(): void
    {
        $this->enableSyslog();

        DB::table('syslog')->insert([
            'device_id' => $this->deviceId(),
            'timestamp' => time(),
            'program' => $this->htmlPayload('MhSyslogProg'),
            'msg' => $this->htmlPayload('MhSyslogMsg'),
            'priority' => 1,
            'facility' => 1,
            'level' => 1,
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=overview');

        $this->assertPayloadInert($page, 'MhSyslogProg');
        $this->assertPayloadInert($page, 'MhSyslogMsg');
    }

    private function enableSyslog(): void
    {
        // The overview query formats the timestamp with MySQL's DATE_FORMAT(); provide the same
        // function to the project's in-memory SQLite connection.
        DB::connection('testing_memory')->getPdo()->sqliteCreateFunction(
            'DATE_FORMAT',
            fn ($timestamp, $format) => date('Y-m-d H:i:s', (int) $timestamp),
            2
        );

        LibrenmsConfig::set('enable_syslog', true);
    }
}
