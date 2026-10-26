<?php

/**
 * The statistics ownership pass runs over a directory taken from the customer's folder. It must
 * not recurse into anything that folder links to outside itself.
 */

declare(strict_types=1);

use Froxlor\Http\Statistics;
use Froxlor\Settings;

require_once __DIR__ . '/../harness/FroxlorCase.php';

final class StatisticsOwnershipSecurityTest extends FroxlorCase
{
    public function testOwnershipPassDoesNotFollowLinkOutOfFolder(): void
    {
        $before = $this->snapshot($this->outsideRoot);
        symlink(rtrim($this->outsideRoot, '/'), rtrim($this->docroot(), '/') . '/awstats');
        Settings::Set('system.traffictool', 'awstats', true);

        try {
            Statistics::makeChownWithNewStats([
                'documentroot' => $this->docroot(),
                'loginname' => 'test1',
                'guid' => $this->agentUid(),
                'deactivated' => '0',
            ]);
        } catch (\Throwable $e) {
            // a refusal is a fine outcome; the assertion below covers the effect either way
        }

        $this->assertOutsideUntouched($before, 'the statistics pass re-owned files outside the customer folder');
    }
}
