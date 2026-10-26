<?php
/**
 * Boots the product's own test setup against the restored /workspace tree. The suites run with
 * the verifier-owned PHPUnit runner, so nothing here comes from the submission's runner config.
 */
$root = '/workspace';
$here = __DIR__;
$storage = $here . '/_craft/storage';

foreach (['runtime', 'logs', 'sessions', 'runtime/compiled_templates', 'runtime/compiled_classes'] as $dir) {
    if (!is_dir($storage . '/' . $dir)) {
        @mkdir($storage . '/' . $dir, 0777, true);
    }
}

ini_set('date.timezone', 'UTC');
date_default_timezone_set('UTC');
ini_set('session.save_path', $storage . '/sessions');

define('CRAFT_ROOT_PATH', $root);
define('CRAFT_TESTS_PATH', $root . '/tests');
define('CRAFT_STORAGE_PATH', $storage);
define('CRAFT_TEMPLATES_PATH', $root . '/tests/_craft/templates');
define('CRAFT_CONFIG_PATH', $here . '/_craft/config');
define('CRAFT_SECRETS_PATH', $here . '/_craft/config/secrets.php');
define('CRAFT_MIGRATIONS_PATH', $root . '/tests/_craft/migrations');
define('CRAFT_TRANSLATIONS_PATH', $root . '/tests/_craft/translations');
define('CRAFT_VENDOR_PATH', $root . '/vendor');

require $root . '/vendor/autoload.php';

\spl_autoload_register(static function (string $class): void {
    $prefix = 'CraftTask\\Harness\\';
    if (!\str_starts_with($class, $prefix)) {
        return;
    }
    $path = dirname(__DIR__) . '/harness/' . \str_replace('\\', '/', \substr($class, \strlen($prefix))) . '.php';
    if (\is_file($path)) {
        require $path;
    }
});

\craft\test\TestSetup::configureCraft();
