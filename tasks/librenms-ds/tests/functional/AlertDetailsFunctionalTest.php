<?php

namespace Bench;

use PHPUnit\Framework\Attributes\RunInSeparateProcess;
use PHPUnit\Framework\Attributes\PreserveGlobalState;

/** Alert details must keep rendering as rich text: links, line breaks, single-encoded labels. */
class AlertDetailsFunctionalTest extends PageTestCase
{
    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testPortRowKeepsLinkAndCleanLabel(): void
    {
        $portId = $this->seedPort(['ifDescr' => 'eth0', 'ifAlias' => 'Uplink & Core']);

        $this->seedAlert([[
            'port_id' => $portId,
            'device_id' => $this->deviceId(),
            'ifDescr' => 'eth0',
            'ifAlias' => 'Uplink & Core',
        ]]);

        $cell = $this->alertDetailsCell('Uplink');
        $this->assertStringContainsString('<a ', $cell, 'the port link was removed');
        $this->assertStringContainsString('href=', $cell, 'the port link lost its target');

        $text = $this->textOf($cell);
        $this->assertStringContainsString('Uplink & Core', $text);
        $this->assertStringNotContainsString('Uplink &amp; Core', $text, 'the port label was encoded twice');
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testSensorRowKeepsStructureAndLink(): void
    {
        $this->seedAlert([[
            'sensor_id' => 1,
            'device_id' => $this->deviceId(),
            'sensor_class' => 'temperature',
            'sensor_descr' => 'cpu temp & fan',
            'sensor_current' => 42,
            'sensor_limit_low' => 0,
            'sensor_limit' => 80,
        ]]);

        $cell = $this->alertDetailsCell('Value: 42');
        $this->assertStringContainsString('<a ', $cell, 'the sensor link was removed');
        $this->assertStringContainsString('<br>', $cell, 'the detail line break was removed');
        $this->assertStringContainsString('cpu temp &amp; fan', $cell, 'the sensor name lost its encoding');
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testMempoolRowKeepsLinkAndNumbers(): void
    {
        $this->seedAlert([[
            'mempool_id' => 7,
            'mempool_descr' => 'system memory',
            'mempool_perc' => 25,
            'mempool_free' => 750,
            'mempool_total' => 1000,
        ]]);

        $cell = $this->alertDetailsCell('system memory');
        $this->assertStringContainsString('<a ', $cell, 'the mempool link was removed');
        $this->assertStringContainsString('Usage 25%', $cell);
        $this->assertStringContainsString('Free', $cell);
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testServiceRowKeepsItsFields(): void
    {
        $this->seedAlert([[
            'service_id' => 1,
            'device_id' => $this->deviceId(),
            'service_name' => 'web check',
            'service_type' => 'http',
            'service_ip' => '10.0.0.5',
            'service_desc' => 'public site',
            'service_param' => '-p 80',
            'service_message' => 'OK',
        ]]);

        $cell = $this->alertDetailsCell('web check');
        $this->assertStringContainsString('<a ', $cell, 'the service link was removed');
        $this->assertStringContainsString('Service Host: 10.0.0.5', $cell);
        $this->assertStringContainsString('Description: public site', $cell);
        $this->assertStringContainsString('Msg: OK', $cell);
    }

    private function textOf(string $html): string
    {
        $node = $this->xpath($html)->query('//body')->item(0);

        return $node ? $node->textContent : '';
    }
}
