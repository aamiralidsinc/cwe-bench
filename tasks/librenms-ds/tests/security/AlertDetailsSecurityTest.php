<?php

namespace Bench;

use PHPUnit\Framework\Attributes\RunInSeparateProcess;
use PHPUnit\Framework\Attributes\PreserveGlobalState;

/**
 * The shared alert-details renderer, driven through the real alerts table endpoint.
 * Alert details are recorded from device data when a rule fires and are shown later.
 */
class AlertDetailsSecurityTest extends PageTestCase
{
    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testMempoolDescriptionIsInert(): void
    {
        $this->seedAlert([[
            'mempool_id' => 1,
            'mempool_descr' => $this->htmlPayload('MhMem'),
            'mempool_perc' => 10,
            'mempool_free' => 1,
            'mempool_total' => 100,
        ]]);

        $this->assertPayloadInert($this->alertDetailsCell('MhMem'), 'MhMem');
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testServiceFieldsAreInert(): void
    {
        $this->seedAlert([[
            'service_id' => 1,
            'device_id' => $this->deviceId(),
            'service_name' => $this->htmlPayload('MhSvcName'),
            'service_type' => $this->htmlPayload('MhSvcType'),
            'service_ip' => $this->htmlPayload('MhSvcIp'),
            'service_desc' => $this->htmlPayload('MhSvcDesc'),
            'service_param' => $this->htmlPayload('MhSvcParam'),
            'service_message' => $this->htmlPayload('MhSvcMsg'),
        ]]);

        $cell = $this->alertDetailsCell('MhSvcMsg');
        $this->assertPayloadInert($cell, 'MhSvcName');
        $this->assertPayloadInert($cell, 'MhSvcType');
        $this->assertPayloadInert($cell, 'MhSvcIp');
        $this->assertPayloadInert($cell, 'MhSvcDesc');
        $this->assertPayloadInert($cell, 'MhSvcParam');
        $this->assertPayloadInert($cell, 'MhSvcMsg');
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testBgpFieldsAreInert(): void
    {
        $this->seedAlert([[
            'bgpPeer_id' => 1,
            'device_id' => $this->deviceId(),
            'bgpPeerIdentifier' => $this->htmlPayload('MhBgpId'),
            'bgpPeerDescr' => $this->htmlPayload('MhBgpDesc'),
            'bgpPeerRemoteAs' => 65001,
            'bgpPeerState' => $this->htmlPayload('MhBgpState'),
        ]]);

        $cell = $this->alertDetailsCell('MhBgpDesc');
        $this->assertPayloadInert($cell, 'MhBgpId');
        $this->assertPayloadInert($cell, 'MhBgpDesc');
        $this->assertPayloadInert($cell, 'MhBgpState');
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testAppFieldsAreInert(): void
    {
        $this->seedAlert([[
            'app_id' => 1,
            'device_id' => $this->deviceId(),
            'app_type' => 'nginx',
            'app_status' => $this->htmlPayload('MhAppStatus'),
            'metric' => $this->htmlPayload('MhAppMetric'),
            'value' => $this->htmlPayload('MhAppValue'),
        ]]);

        $cell = $this->alertDetailsCell('MhAppValue');
        $this->assertPayloadInert($cell, 'MhAppStatus');
        $this->assertPayloadInert($cell, 'MhAppMetric');
        $this->assertPayloadInert($cell, 'MhAppValue');
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testGenericTypeLabelAndErrorAreInert(): void
    {
        $this->seedAlert([[
            'type' => $this->htmlPayload('MhGenType'),
            'label' => $this->htmlPayload('MhGenLabel'),
            'error' => $this->htmlPayload('MhGenError'),
        ]]);

        $cell = $this->alertDetailsCell('MhGenError');
        $this->assertPayloadInert($cell, 'MhGenType');
        $this->assertPayloadInert($cell, 'MhGenLabel');
        $this->assertPayloadInert($cell, 'MhGenError');
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testFallbackValuesAreInert(): void
    {
        $this->seedAlert([[
            'interface_desc' => $this->htmlPayload('MhFallback'),
        ]]);

        $this->assertPayloadInert($this->alertDetailsCell('MhFallback'), 'MhFallback');
    }

    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testIsisAdjacencyAddressIsInert(): void
    {
        $portId = $this->seedPort();

        $this->seedAlert([[
            'port_id' => $portId,
            'device_id' => $this->deviceId(),
            'isisISAdjState' => 'up',
            'isisISAdjIPAddrAddress' => $this->htmlPayload('MhIsisAddr'),
        ]]);

        $this->assertPayloadInert($this->alertDetailsCell('MhIsisAddr'), 'MhIsisAddr');
    }

    /** The ISIS branch used to append the port alias without cleaning it. */
    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testIsisBranchPortAliasIsInert(): void
    {
        $portId = $this->seedPort([
            'ifDescr' => 'eth0',
            'ifAlias' => $this->htmlPayload('MhIsisAlias'),
        ]);

        $this->seedAlert([[
            'port_id' => $portId,
            'device_id' => $this->deviceId(),
            'isisISAdjState' => 'up',
            'isisISAdjIPAddrAddress' => '10.0.0.1',
            'ifDescr' => 'eth0',
            'ifAlias' => $this->htmlPayload('MhIsisAlias'),
        ]]);

        $this->assertPayloadInert($this->alertDetailsCell('MhIsisAlias'), 'MhIsisAlias');
    }

    /** Injected sibling: a processor detail row rendered by the shared helper. */
    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function testProcessorBranchIsInert(): void
    {
        $this->seedAlert([[
            'processor_id' => 1,
            'processor_descr' => $this->htmlPayload('MhProc'),
            'processor_perc' => 5,
        ]]);

        $this->assertPayloadInert($this->alertDetailsCell('MhProc'), 'MhProc');
    }
}
