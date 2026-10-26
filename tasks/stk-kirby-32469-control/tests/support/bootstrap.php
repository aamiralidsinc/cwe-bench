<?php
/**
 * Test bootstrap for the hidden suites. The verifier image is separate from the agent image:
 * /workspace is the agent's restored project, with its vendor tree.
 */
namespace Kirby\Api {
    /**
     * PHP refuses to move a file that did not arrive through a real multipart request, so the
     * project's own suites acknowledge that this builtin cannot run outside HTTP. The hidden
     * suites drive the real API routes in-process; this stand-in performs the same file move.
     */
    function move_uploaded_file(string $from, string $to): bool
    {
        if (is_file($from) === false) {
            return false;
        }

        return copy($from, $to);
    }
}

namespace {
    require '/workspace/vendor/autoload.php';

    define('KIRBY_DIR', '/workspace');
    define('KIRBY_TESTING', true);
    define('KIRBY_TMP_DIR', sys_get_temp_dir() . '/kirby-hidden');

    \Kirby\Cms\App::$enableWhoops = false;
    \Kirby\Cms\Core::$indexRoot = '/dev/null';

    require __DIR__ . '/Scenario.php';
}
