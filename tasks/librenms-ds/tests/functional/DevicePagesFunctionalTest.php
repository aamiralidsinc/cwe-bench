<?php

namespace Bench;

/** Legitimate device values must keep rendering, and tooltips must keep working. */
class DevicePagesFunctionalTest extends PageTestCase
{
    public function testStoragePageKeepsDescriptionAndTooltip(): void
    {
        $this->seedStorage(['storage_descr' => "Data & Logs 'A'"]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=health/metric=storage');

        $text = $this->bodyText($page);
        $this->assertStringContainsString("Data & Logs 'A'", $text);
        $this->assertStringNotContainsString('&amp;', $text, 'the description was encoded twice');
    }

    public function testBgpPageKeepsDescription(): void
    {
        $this->seedBgpPeer(['bgpPeerDescr' => "Peer & Edge 'A'", 'astext' => 'AS & Co']);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=routing/proto=bgp');

        $text = $this->bodyText($page);
        $this->assertStringContainsString("Peer & Edge 'A'", $text);
        $this->assertStringContainsString('AS & Co', $text);
    }

    public function testSlaListKeepsTagAndOwner(): void
    {
        $this->seedSla(['tag' => "T & 'A'", 'owner' => "O & 'B'"]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=slas/id=0');

        $text = $this->bodyText($page);
        $this->assertStringContainsString("T & 'A'", $text);
        $this->assertStringContainsString("O & 'B'", $text);
        $this->assertStringNotContainsString('&amp;', $text, 'the SLA name was encoded twice');
    }

    public function testInventoryKeepsDescription(): void
    {
        $this->seedHrDevice(['hrDeviceDescr' => "CPU & 'A'"]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=inventory');

        $this->assertStringContainsString("CPU & 'A'", $this->bodyText($page));
        $this->assertTooltipContains($page, 'CPU', 'graph.php');
    }

    private function bodyText(string $html): string
    {
        $node = $this->xpath($html)->query('//body')->item(0);

        return $node ? $node->textContent : '';
    }

    private function assertTooltipContains(string $html, string $needle, string $also): void
    {
        $found = false;
        foreach ($this->xpath($html)->query('//@*') as $attribute) {
            if (str_starts_with($attribute->nodeName, 'on') && str_contains($attribute->value, 'overlib(')) {
                if (str_contains($attribute->value, $needle) && str_contains($attribute->value, $also)) {
                    $found = true;
                    break;
                }
            }
        }

        $this->assertTrue($found, 'the hover tooltip no longer shows its description and graph');
    }
}
