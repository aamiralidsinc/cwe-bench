<?php

/**
 * Verifier bootstrap for the hidden suites.
 *
 * The application code under test is whatever the agent left in /workspace; the tests, this
 * bootstrap and the harness live only in the verifier image.
 */

declare(strict_types=1);

$workspace = getenv('PA_WORKSPACE');
if (!is_string($workspace) || $workspace === '') {
    $workspace = '/workspace';
}

date_default_timezone_set('UTC');
ini_set('display_errors', '1');
error_reporting(E_ALL & ~E_DEPRECATED);

require $workspace . '/vendor/autoload.php';
require_once __DIR__ . '/../harness/ProvisioningCase.php';
