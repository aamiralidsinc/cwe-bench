<?php

namespace Bench;

/** Device tabs that print values polled from the device. */
class DevicePageSecurityTest extends PageTestCase
{
    public function testProcessTableIsInert(): void
    {
        $this->seedProcess([
            'user' => $this->htmlPayload('MhProcUser'),
            'command' => $this->htmlPayload('MhProcCmd'),
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=processes');

        $this->assertPayloadInert($page, 'MhProcUser');
        $this->assertPayloadInert($page, 'MhProcCmd');
    }

    /** Injected sibling: the full command is also placed in a hover handler. */
    public function testProcessCommandTooltipIsInert(): void
    {
        $this->seedProcess(['command' => $this->htmlPayload('MhProcTip')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=processes');

        $this->assertPayloadInert($page, 'MhProcTip');
    }

    public function testPortVlanFieldsAreInert(): void
    {
        $portId = $this->seedPort();
        $this->seedVlan(['vlan_name' => $this->htmlPayload('MhVlanName')]);
        $this->seedPortVlan($portId);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=port/port=' . $portId . '/view=vlans');

        $this->assertPayloadInert($page, 'MhVlanName');
    }

    public function testPortSensorDescriptionIsInert(): void
    {
        $portId = $this->seedPort(['ifIndex' => 5]);
        $this->seedSensor([
            'entPhysicalIndex' => 5,
            'entPhysicalIndex_measured' => 'ports',
            'sensor_descr' => $this->htmlPayload('MhPortSensor'),
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=port/port=' . $portId . '/view=sensors');

        $this->assertPayloadInert($page, 'MhPortSensor');
    }

    public function testBgpPeerFieldsAreInert(): void
    {
        $this->seedBgpPeer([
            'bgpPeerDescr' => $this->htmlPayload('MhBgpDescr'),
            'bgpPeerLastErrorText' => $this->htmlPayload('MhBgpError'),
            'astext' => $this->htmlPayload('MhBgpAs'),
            'bgpPeerState' => $this->htmlPayload('MhBgpState'),
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=routing/proto=bgp');

        $this->assertPayloadInert($page, 'MhBgpDescr');
        $this->assertPayloadInert($page, 'MhBgpError');
        $this->assertPayloadInert($page, 'MhBgpAs');
        $this->assertPayloadInert($page, 'MhBgpState');
    }

    public function testVrfFieldsAreInert(): void
    {
        $this->seedVrf([
            'vrf_name' => $this->htmlPayload('MhVrfName'),
            'mplsVpnVrfDescription' => $this->htmlPayload('MhVrfDescr'),
            'mplsVpnVrfRouteDistinguisher' => '65001:99',
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=routing/proto=vrf');

        $this->assertPayloadInert($page, 'MhVrfName');
        $this->assertPayloadInert($page, 'MhVrfDescr');
    }

    public function testIsisAdjacencyFieldsAreInert(): void
    {
        $this->seedPort(['ifIndex' => 5]);
        $this->seedIsis([
            'isisISAdjIPAddrAddress' => $this->htmlPayload('MhIsisIp'),
            'isisISAdjNeighSysID' => $this->htmlPayload('MhIsisSysId'),
            'isisISAdjAreaAddress' => $this->htmlPayload('MhIsisArea'),
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=routing/proto=isis');

        $this->assertPayloadInert($page, 'MhIsisIp');
        $this->assertPayloadInert($page, 'MhIsisSysId');
        $this->assertPayloadInert($page, 'MhIsisArea');
    }

    public function testMplsFieldsAreInert(): void
    {
        $this->seedMpls([
            'mplsLspName' => $this->htmlPayload('MhMplsLsp'),
        ]);
        // rewrite the vrf name too
        \Illuminate\Support\Facades\DB::table('vrfs')
            ->where('device_id', $this->deviceId())
            ->update(['vrf_name' => $this->htmlPayload('MhMplsVrf')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=routing/proto=mpls');

        $this->assertPayloadInert($page, 'MhMplsLsp');
        $this->assertPayloadInert($page, 'MhMplsVrf');
    }

    public function testSlaDetailIsInert(): void
    {
        $slaId = $this->seedSla([
            'tag' => $this->htmlPayload('MhSlaTag'),
            'owner' => $this->htmlPayload('MhSlaOwner'),
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=slas/id=' . $slaId);

        $this->assertPayloadInert($page, 'MhSlaTag');
        $this->assertPayloadInert($page, 'MhSlaOwner');
    }

    /** SLA list: the linked (jitter-type) rows used to bypass the escaping branch. */
    public function testSlaListLinkedRowIsInert(): void
    {
        $this->seedSla([
            'rtt_type' => 'jitter',
            'tag' => $this->htmlPayload('MhSlaListTag'),
            'owner' => $this->htmlPayload('MhSlaListOwner'),
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=slas/id=0');

        $this->assertPayloadInert($page, 'MhSlaListTag');
        $this->assertPayloadInert($page, 'MhSlaListOwner');
    }

    public function testInventoryDescriptionIsInert(): void
    {
        $this->seedHrDevice(['hrDeviceDescr' => $this->htmlPayload('MhInventory')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=inventory');

        $this->assertPayloadInert($page, 'MhInventory');
    }

    /** The inventory processor link also puts the description in a hover handler. */
    public function testInventoryTooltipIsInert(): void
    {
        $this->seedHrDevice(['hrDeviceDescr' => $this->htmlPayload('MhInvTip')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=inventory');

        $this->assertPayloadInert($page, 'MhInvTip');
    }

    public function testWirelessSensorDescriptionIsInert(): void
    {
        $this->seedWirelessSensor(['sensor_descr' => $this->htmlPayload('MhWireless')]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=wireless/metric=rssi');

        $this->assertPayloadInert($page, 'MhWireless');
    }
}
