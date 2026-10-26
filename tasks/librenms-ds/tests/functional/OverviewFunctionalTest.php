<?php

namespace Bench;

/** Overview panels must keep their hover tooltips and descriptions. */
class OverviewFunctionalTest extends PageTestCase
{
    public function testOverviewStorageKeepsDescriptionAndTooltip(): void
    {
        $this->seedStorage(['storage_descr' => "Vol & 'A'"]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=overview');

        $this->assertStringContainsString("Vol & 'A'", $this->bodyText($page));
        $this->assertTooltipContains($page, 'Vol', 'graph.php');
    }

    public function testOverviewMempoolKeepsDescriptionAndTooltip(): void
    {
        $this->seedMempool(['mempool_descr' => "Mem & 'B'"]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=overview');

        $this->assertStringContainsString("Mem & 'B'", $this->bodyText($page));
        $this->assertTooltipContains($page, 'Mem', 'graph.php');
    }

    public function testOverviewSyslogKeepsFields(): void
    {
        \Illuminate\Support\Facades\DB::connection('testing_memory')->getPdo()->sqliteCreateFunction(
            'DATE_FORMAT',
            fn ($timestamp, $format) => date('Y-m-d H:i:s', (int) $timestamp),
            2
        );
        \App\Facades\LibrenmsConfig::set('enable_syslog', true);

        \Illuminate\Support\Facades\DB::table('syslog')->insert([
            'device_id' => $this->deviceId(),
            'timestamp' => time(),
            'program' => 'sshd',
            'msg' => 'Accepted publickey for admin & guest',
            'priority' => 1,
            'facility' => 1,
            'level' => 1,
        ]);

        $page = $this->fetchPage('/device/device=' . $this->deviceId() . '/tab=overview');

        $text = $this->bodyText($page);
        $this->assertStringContainsString('sshd', $text);
        $this->assertStringContainsString('Accepted publickey for admin & guest', $text);
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
            if (str_starts_with($attribute->nodeName, 'on')
                && str_contains($attribute->value, 'overlib(')
                && str_contains($attribute->value, $needle)
                && str_contains($attribute->value, $also)) {
                $found = true;
                break;
            }
        }

        $this->assertTrue($found, 'the overview tooltip no longer shows its description and graph');
    }
}
