<?php
// Verifier bootstrap: the restored workspace's own Composer autoloader.
declare(strict_types=1);
require_once getenv('PPS_AUTOLOAD') ?: '/workspace/vendor/autoload.php';
require_once __DIR__ . '/Harness.php';
