<?php

namespace Bench;

/** Device health tabs: descriptions polled from the device, in text and in hover tooltips. */
class DeviceHealthSecurityTest extends PageTestCase
{
    public function testStorageDescriptionIsInert(): void
    {
        $this->seedStorage(['storage_descr' => $this->htmlPayload('MhStorText')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=health/metric=storage');

        $this->assertPayloadInert($page, 'MhStorText');
    }

    public function testSensorDescriptionIsInert(): void
    {
        $this->seedSensor(['sensor_descr' => $this->htmlPayload('MhSensor')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=health/metric=temperature');

        $this->assertPayloadInert($page, 'MhSensor');
    }

    public function testIpmiSensorDescriptionIsInert(): void
    {
        $this->seedSensor([
            'poller_type' => 'ipmi',
            'sensor_descr' => $this->htmlPayload('MhIpmi'),
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=health/metric=temperature');

        $this->assertPayloadInert($page, 'MhIpmi');
    }

    public function testMempoolDescriptionIsInert(): void
    {
        $this->seedMempool(['mempool_descr' => $this->htmlPayload('MhMempool')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=health/metric=mempool');

        $this->assertPayloadInert($page, 'MhMempool');
    }

    public function testProcessorDescriptionIsInert(): void
    {
        $this->seedProcessor(['processor_descr' => $this->htmlPayload('MhProcessor')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=health/metric=processor');

        $this->assertPayloadInert($page, 'MhProcessor');
    }

    public function testDiskioDescriptionIsInert(): void
    {
        $this->seedDiskio(['diskio_descr' => $this->htmlPayload('MhDiskio')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=health/metric=diskio');

        $this->assertPayloadInert($page, 'MhDiskio');
    }
}
