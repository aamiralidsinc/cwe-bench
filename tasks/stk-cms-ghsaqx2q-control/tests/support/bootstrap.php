<?php

declare(strict_types=1);

/*
 * Shared bootstrap for the hidden suites.
 *
 * The application under test is whatever the solver left in /workspace. The database is a
 * throwaway MySQL schema started by test.sh; a stock Craft install is created here once per
 * suite, with one section that the element-index suite can address.
 */

const CRAFT_TESTS_PATH = '/workspace/tests';
const CRAFT_STORAGE_PATH = '/workspace/tests/_craft/storage';
const CRAFT_TEMPLATES_PATH = '/workspace/tests/_craft/templates';
const CRAFT_CONFIG_PATH = '/workspace/tests/_craft/config';
const CRAFT_SECRETS_PATH = CRAFT_CONFIG_PATH . '/secrets.php';
const CRAFT_MIGRATIONS_PATH = '/workspace/tests/_craft/migrations';
const CRAFT_TRANSLATIONS_PATH = '/workspace/tests/_craft/translations';
define('CRAFT_VENDOR_PATH', '/workspace/vendor');
define('CRAFT_ROOT_PATH', '/workspace');
$devMode = true;

require CRAFT_VENDOR_PATH . '/autoload.php';
require_once __DIR__ . '/ProbeBehavior.php';
require_once __DIR__ . '/ProbeHandler.php';
require_once __DIR__ . '/Harness.php';

use craft\migrations\Install;
use craft\models\Site;
use craft\test\TestSetup;

TestSetup::configureCraft();

// The runner lives outside the project (/opt/phpunit.phar), and Craft derives @webroot from
// the running script. Point it at a writable project directory so the app can create its
// resource folder when it boots as the unprivileged test user.
\Craft::setAlias('@webroot', '/workspace/tests/_craft');

$app = \Craft::createObject(TestSetup::createTestCraftObjectConfig());

if (!$app->getIsInstalled()) {
    ob_start();
    try {
        $site = new Site([
            'name' => 'Craft bench site',
            'handle' => 'default',
            'hasUrls' => true,
            'baseUrl' => TestSetup::SITE_URL,
            'language' => 'en-US',
            'primary' => true,
        ]);
        $migration = new Install([
            'db' => $app->getDb(),
            'username' => TestSetup::USERNAME,
            'password' => 'craftcms2018!!',
            'email' => 'support@craftcms.com',
            'site' => $site,
        ]);
        $migration->up(true);
        $app->setIsInstalled();
    } finally {
        ob_end_clean();
    }
}

\CraftBench\Harness::init($app);
