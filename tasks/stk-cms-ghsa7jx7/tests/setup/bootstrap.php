<?php
/**
 * Offline bootstrap for the hidden PHPUnit suites.
 *
 * Builds the real Craft web application against the project tree in /workspace,
 * without a database (the control-panel services used by the field layout code
 * are independent of persistence), and restores PHPUnit's own error handlers
 * after Craft registers its error handler.
 */
error_reporting(E_ALL & ~E_DEPRECATED & ~E_USER_DEPRECATED);
ini_set('display_errors', '1');
ini_set('date.timezone', 'UTC');
date_default_timezone_set('UTC');

define('HTEST_ROOT', dirname(__DIR__, 2));
define('CRAFT_ROOT_PATH', HTEST_ROOT);
define('CRAFT_TESTS_PATH', HTEST_ROOT . '/tests');
define('CRAFT_STORAGE_PATH', HTEST_ROOT . '/.htests/storage');
define('CRAFT_TEMPLATES_PATH', HTEST_ROOT . '/.htests/templates');
define('CRAFT_CONFIG_PATH', HTEST_ROOT . '/.htests/config');
define('CRAFT_MIGRATIONS_PATH', HTEST_ROOT . '/.htests/migrations');
define('CRAFT_TRANSLATIONS_PATH', HTEST_ROOT . '/.htests/translations');
define('CRAFT_VENDOR_PATH', HTEST_ROOT . '/vendor');

foreach (['storage', 'storage/runtime', 'storage/logs', 'templates', 'config', 'migrations', 'translations'] as $dir) {
    @mkdir(CRAFT_STORAGE_PATH . substr($dir, 7), 0777, true);
}
@mkdir(HTEST_ROOT . '/.htests/templates', 0777, true);
@mkdir(HTEST_ROOT . '/.htests/config', 0777, true);
@mkdir(HTEST_ROOT . '/.htests/migrations', 0777, true);
@mkdir(HTEST_ROOT . '/.htests/translations', 0777, true);

require HTEST_ROOT . '/vendor/autoload.php';
require HTEST_ROOT . '/lib/yii2/Yii.php';
require HTEST_ROOT . '/src/Craft.php';

foreach ([
    '@craftcms' => HTEST_ROOT,
    '@root' => HTEST_ROOT,
    '@lib' => HTEST_ROOT . '/lib',
    '@craft' => HTEST_ROOT . '/src',
    '@appicons' => HTEST_ROOT . '/src/icons',
    '@vendor' => HTEST_ROOT . '/vendor',
    '@config' => CRAFT_CONFIG_PATH,
    '@storage' => CRAFT_STORAGE_PATH,
    '@templates' => CRAFT_TEMPLATES_PATH,
    '@translations' => CRAFT_TRANSLATIONS_PATH,
    '@tests' => CRAFT_TESTS_PATH,
    '@webroot' => HTEST_ROOT,
    '@web' => 'http://localhost',
] as $alias => $path) {
    Craft::setAlias($alias, $path);
}

$config = \craft\helpers\ArrayHelper::merge(
    require HTEST_ROOT . '/src/config/app.php',
    require HTEST_ROOT . '/src/config/app.web.php',
);
$config['class'] = \craft\web\Application::class;
$config['id'] = 'htest';
$config['basePath'] = HTEST_ROOT . '/src';
$config['runtimePath'] = CRAFT_STORAGE_PATH . '/runtime';
$config['vendorPath'] = CRAFT_VENDOR_PATH;
$config['isInstalled'] = false;
$config['env'] = 'test';
$config['components']['config'] = new \craft\services\Config();

$app = Craft::createObject($config);
Craft::$app = $app;

// Craft registers its own PHP error and exception handlers during application
// construction; hand them back so PHPUnit reports test failures normally.
restore_error_handler();
restore_exception_handler();

require __DIR__ . '/support.php';
