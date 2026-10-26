<?php

/**
 * The statistics ownership pass must keep doing its job for a real statistics directory inside
 * the customer's folder: the customer must still be made the owner.
 */

declare(strict_types=1);

use Froxlor\Http\Statistics;
use Froxlor\Settings;

require_once __DIR__ . '/../harness/FroxlorCase.php';

final class StatisticsOwnershipFunctionalTest extends FroxlorCase
{
    public function testOwnershipPassStillRunsForRealDirectory(): void
    {
        // The prepared area stands in for the customer's folder here; its canary starts with a
        // different group, so a recursive ownership change is visible.
        $stats = rtrim($this->outsideRoot, '/') . '/awstats/';
        mkdir($stats, 0777, true);
        rename($this->preexistingCanary(), $stats . 'canary.txt');
        $path = $stats . 'canary.txt';
        clearstatcache(true);
        $this->assertSame(0, lstat($path)['gid'], 'prepared canary no longer starts outside the customer group');

        Settings::Set('system.traffictool', 'awstats', true);
        Statistics::makeChownWithNewStats([
            'documentroot' => $this->outsideRoot . '/',
            'loginname' => 'test1',
            'guid' => $this->agentUid(),
            'deactivated' => '0',
        ]);

        clearstatcache(true);
        $st = lstat($path);
        $this->assertSame($this->agentUid(), (int)$st['gid'], 'the statistics directory was not handed to the customer');
    }
}
