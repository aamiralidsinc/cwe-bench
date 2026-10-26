<?php

/**
 * Verifier bootstrap for the phpMyFAQ suite.
 *
 * Installs a throw-away SQLite database from the submission tree that is restored in
 * /workspace, then makes the application classes available to the hidden tests. The
 * application code under test is whatever the agent left in /workspace; the tests and this
 * bootstrap live only in the verifier image.
 */

declare(strict_types=1);

use phpMyFAQ\Setup\Installer;
use phpMyFAQ\Strings;
use phpMyFAQ\System;
use Symfony\Component\HttpFoundation\Request;

$workspace = getenv('PMF_WORKSPACE');
if (!is_string($workspace) || $workspace === '') {
    $workspace = '/workspace';
}

date_default_timezone_set('Europe/Berlin');

ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL & ~E_DEPRECATED);

define('PMF_ROOT_DIR', $workspace . '/phpmyfaq');
define('PMF_TEST_DIR', __DIR__);
define('PMF_CONFIG_DIR', __DIR__ . '/content/core/config');
define('PMF_CONTENT_DIR', __DIR__ . '/content');
define('PMF_LOG_DIR', __DIR__ . '/logs/phpmyfaq.log');
define('IS_VALID_PHPMYFAQ', true);

$_SERVER['HTTP_HOST'] = 'localhost';
$_SERVER['SERVER_NAME'] = 'localhost';

foreach ([__DIR__ . '/content', PMF_CONFIG_DIR, dirname(PMF_LOG_DIR)] as $directory) {
    if (!is_dir($directory)) {
        @mkdir($directory, 0o777, true);
    }
}

if (!file_exists(PMF_LOG_DIR)) {
    @touch(PMF_LOG_DIR);
}

require PMF_ROOT_DIR . '/content/core/config/constants.php';

define('PMF_SRC_DIR', PMF_ROOT_DIR . '/src');
define('PMF_TRANSLATION_DIR', PMF_ROOT_DIR . '/translations');

require PMF_TRANSLATION_DIR . '/language_en.php';

// The submission's own Composer autoloader maps phpMyFAQ\ to the product sources.
require PMF_ROOT_DIR . '/src/libs/autoload.php';

// A fresh database for every test process.
foreach ([
    __DIR__ . '/test.db',
    __DIR__ . '/test.db-journal',
    __DIR__ . '/test.db-wal',
    __DIR__ . '/test.db-shm',
    PMF_CONFIG_DIR . '/database.php',
] as $leftover) {
    @unlink($leftover);
}

$setup = [
    'dbServer' => __DIR__ . '/test.db',
    'dbType' => 'pdo_sqlite',
    'dbPort' => null,
    'dbDatabaseName' => '',
    'loginname' => 'admin',
    'password' => 'password',
    'password_retyped' => 'password',
    'rootDir' => __DIR__,
    'mainUrl' => 'https://localhost/',
];

Strings::init();

Request::setTrustedHosts(['^.*$']);

try {
    $installer = new Installer(new System());
    $installer->startInstall($setup);
} catch (Throwable $exception) {
    // One retry: a leftover SQLite journal from an aborted run can make the first attempt fail.
    foreach ([__DIR__ . '/test.db', __DIR__ . '/test.db-journal', PMF_CONFIG_DIR . '/database.php'] as $leftover) {
        @unlink($leftover);
    }
    usleep(200000);

    try {
        $installer = new Installer(new System());
        $installer->startInstall($setup);
    } catch (Throwable $retryException) {
        fwrite(STDERR, 'bootstrap install failed: ' . $retryException->getMessage() . PHP_EOL);
        exit(1);
    }
}

require PMF_CONFIG_DIR . '/database.php';
