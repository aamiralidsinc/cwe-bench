<?php

namespace Bench;

/** The global routing pages render the same device tables a second time. */
class GlobalRoutingSecurityTest extends PageTestCase
{
    public function testGlobalBgpFieldsAreInert(): void
    {
        $this->seedBgpPeer([
            'bgpPeerDescr' => $this->htmlPayload('MhGlobalBgpDescr'),
            'bgpPeerLastErrorText' => $this->htmlPayload('MhGlobalBgpError'),
            'astext' => $this->htmlPayload('MhGlobalBgpAs'),
            'bgpPeerState' => $this->htmlPayload('MhGlobalBgpState'),
        ]);

        $page = $this->fetchPage('/routing/protocol=bgp');

        $this->assertPayloadInert($page, 'MhGlobalBgpDescr');
        $this->assertPayloadInert($page, 'MhGlobalBgpError');
        $this->assertPayloadInert($page, 'MhGlobalBgpAs');
        $this->assertPayloadInert($page, 'MhGlobalBgpState');
    }

    public function testGlobalVrfFieldsAreInert(): void
    {
        $this->seedVrf([
            'vrf_name' => $this->htmlPayload('MhGlobalVrfName'),
            'mplsVpnVrfDescription' => $this->htmlPayload('MhGlobalVrfDescr'),
            'mplsVpnVrfRouteDistinguisher' => '65001:99',
        ]);

        $page = $this->fetchPage('/routing/protocol=vrf');

        $this->assertPayloadInert($page, 'MhGlobalVrfName');
        $this->assertPayloadInert($page, 'MhGlobalVrfDescr');
    }
}
