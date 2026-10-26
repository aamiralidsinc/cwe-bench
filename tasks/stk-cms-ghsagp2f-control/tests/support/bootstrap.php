<?php
/**
 * Hidden verification bootstrap. Builds a Craft web application against the restored
 * /workspace tree, using the harness' own config, storage and templates directories so
 * nothing in the agent's tests/ tree is trusted.
 */

define('CRAFT_ROOT_PATH', '/workspace');
define('CRAFT_TESTS_PATH', '/workspace/.htests');
define('CRAFT_STORAGE_PATH', '/workspace/.htests/storage');
define('CRAFT_TEMPLATES_PATH', '/workspace/.htests/templates');
define('CRAFT_CONFIG_PATH', '/workspace/.htests/config');
define('CRAFT_SECRETS_PATH', CRAFT_CONFIG_PATH . '/secrets.php');
define('CRAFT_MIGRATIONS_PATH', '/workspace/.htests/migrations');
define('CRAFT_TRANSLATIONS_PATH', '/workspace/.htests/translations');
define('CRAFT_VENDOR_PATH', '/workspace/vendor');

require CRAFT_VENDOR_PATH . '/autoload.php';

\craft\test\TestSetup::configureCraft();

/**
 * Boots a fresh Craft web application for one test case.
 *
 * @param array<string,string> $server $_SERVER overrides (host, path) for request-shaped tests
 */
function craft_boot(array $server = []): \craft\web\Application
{
    foreach ($server as $key => $value) {
        $_SERVER[$key] = $value;
    }

    /** @var \craft\web\Application $app */
    $app = \craft\test\TestSetup::warmCraft();
    \Craft::$app = $app;
    \Yii::$app = $app;
    $app->setIsInstalled();
    $app->getSites()->refreshSites();
    $app->getProjectConfig()->reset();

    return $app;
}
