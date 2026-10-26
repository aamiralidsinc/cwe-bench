<?php

/**
 * Verifier bootstrap for the hidden suites.
 *
 * The application code under test is whatever the agent left in /workspace. The fixtures below
 * are ordinary panel rows: one administrator, one customer, and the settings a stock install
 * ships with, adjusted only where a suite needs a different value. Each grading group gets its
 * own database (created and loaded from the pinned schema by test.sh before any test runs).
 */

declare(strict_types=1);

$ws = getenv('FROX_WORKSPACE');
if (!is_string($ws) || $ws === '') {
    $ws = '/workspace';
}
$run = getenv('FROX_RUN');
if (!is_string($run) || $run === '') {
    $run = '/tmp/frox-run';
}
$dbHost = getenv('FROX_DB_HOST') ?: '127.0.0.1';
$dbPort = getenv('FROX_DB_PORT') ?: '3306';
$dbUser = getenv('FROX_DB_USER') ?: 'frx';
$dbPass = getenv('FROX_DB_PASS') ?: 'frx-test-pass';
$dbName = getenv('FROX_DB_NAME') ?: 'froxlor_test';

define('DEV_FROXLOR', 1);
define('TRAVIS_CI', 1);
define('FROX_RUN_DIR', $run);
define('FROX_WORKSPACE_DIR', $ws);

date_default_timezone_set('UTC');
ini_set('display_errors', '1');
error_reporting(E_ALL & ~E_DEPRECATED);

// The panel reads its database credentials from this file on every connection.
$userdata = "<?php\n"
    . "\$sql = [\n"
    . "    'user' => '" . $dbUser . "',\n"
    . "    'password' => '" . $dbPass . "',\n"
    . "    'host' => '" . $dbHost . "',\n"
    . "    'port' => '" . $dbPort . "',\n"
    . "    'db' => '" . $dbName . "',\n"
    . "    'debug' => true,\n"
    . "];\n"
    . "\$sql_root = [\n"
    . "    0 => [\n"
    . "        'caption' => 'Test default',\n"
    . "        'user' => 'root',\n"
    . "        'password' => '',\n"
    . "        'host' => '127.0.0.1',\n"
    . "    ],\n"
    . "];\n";
file_put_contents($ws . '/lib/userdata.inc.php', $userdata);

require $ws . '/vendor/autoload.php';
require_once $ws . '/lib/functions.php';
require_once $ws . '/lib/tables.inc.php';

use Froxlor\Database\Database;
use Froxlor\FroxlorLogger;
use Froxlor\Settings;

require_once __DIR__ . '/../harness/FroxlorCase.php';

// Local filesystem layout the fixtures point at.
@mkdir($run . '/docroots/test1', 0777, true);
@mkdir($run . '/outside', 0777, true);

$stmt = Database::prepare("SELECT COUNT(*) AS `c` FROM `" . TABLE_PANEL_ADMINS . "`");
$has_admin = Database::pexecute_first($stmt);
if (!$has_admin || (int)$has_admin['c'] === 0) {
    // One administrator with every resource unlimited, as a fresh installation's first admin.
    Database::query("INSERT INTO `" . TABLE_PANEL_ADMINS . "` SET
        `adminid` = 1, `loginname` = 'admin', `password` = 'x', `name` = 'Administrator',
        `email` = 'admin@example.test', `def_language` = 'English', `ip` = '-1',
        `customers` = -1, `customers_see_all` = 1, `domains` = -1, `caneditphpsettings` = 1,
        `change_serversettings` = 1, `diskspace` = -1024, `mysqls` = -1, `emails` = -1,
        `email_accounts` = -1, `email_forwarders` = -1, `email_quota` = -1, `ftps` = -1,
        `subdomains` = -1, `traffic` = -1048576");

    // One customer whose document root is the prefix plus the login name, as the panel builds it.
    Database::query("INSERT INTO `" . TABLE_PANEL_CUSTOMERS . "` SET
        `customerid` = 1, `loginname` = 'test1', `password` = 'x', `adminid` = 1,
        `name` = 'Test', `firstname` = 'Testman', `email` = 'test1@example.test',
        `customernumber` = '1337', `def_language` = 'English', `documentroot` = '" . $run . "/docroots/test1/',
        `guid` = 10000, `diskspace` = -1024, `traffic` = -1048576, `mysqls` = -1, `emails` = -1,
        `email_accounts` = -1, `email_forwarders` = -1, `email_quota` = -1, `ftps` = -1,
        `subdomains` = -1, `deactivated` = 0, `phpenabled` = 1, `allowed_phpconfigs` = '', `allowed_mysqlserver` = ''");
}

// Settings the stock installer ships, with the few values every suite needs.
Settings::Set('system.documentroot_prefix', $run . '/docroots/', true);
Settings::Set('system.exportenabled', 1, true);
Settings::Set('panel.customer_hide_options', '', true);
Settings::Set('system.traffictool', 'awstats', true);
Settings::Set('phpfpm.enabled', 0, true);
Settings::Set('system.mod_fcgid', 0, true);
Settings::Set('logger.enabled', 1, true);
Settings::Set('logger.logtypes', 'mysql', true);
Settings::Set('logger.severity', '0', true);
Settings::Set('logger.log_cron', '1', true);

$admin_stmt = Database::prepare("SELECT * FROM `" . TABLE_PANEL_ADMINS . "` WHERE `adminid` = 1");
$admin_userdata = Database::pexecute_first($admin_stmt);
$admin_userdata['adminsession'] = 1;
$GLOBALS['admin_userdata'] = $admin_userdata;

FroxlorLogger::getInstanceOf($admin_userdata);
