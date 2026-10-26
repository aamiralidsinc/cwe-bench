<?php

namespace Bench;

/** Overview panels show device descriptions through hover tooltips. */
class OverviewSecurityTest extends PageTestCase
{
    public function testOverviewStorageIsInert(): void
    {
        $this->seedStorage(['storage_descr' => $this->htmlPayload('MhOvStorage')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=overview');

        $this->assertPayloadInert($page, 'MhOvStorage');
    }

    public function testOverviewStorageTooltipQuoteCannotBreakOut(): void
    {
        $this->seedStorage(['storage_descr' => $this->quotePayload('MhOvQuote')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=overview');

        $this->assertQuoteInert($page, 'MhOvQuote');
    }

    public function testOverviewMempoolIsInert(): void
    {
        $this->seedMempool(['mempool_descr' => $this->htmlPayload('MhOvMempool')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=overview');

        $this->assertPayloadInert($page, 'MhOvMempool');
    }

    public function testOverviewSensorIsInert(): void
    {
        $this->seedSensor(['sensor_descr' => $this->htmlPayload('MhOvSensor')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=overview');

        $this->assertPayloadInert($page, 'MhOvSensor');
    }
}
