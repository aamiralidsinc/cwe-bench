<?php

// The verifier runs the hidden tests from /workspace/.htests against the application restored
// at /workspace. Reuse the application's own Composer autoloader, then register a tiny PSR-4
// autoloader for the CweTests\ namespace that holds this task's base TestCase.

putenv('GRAV_ROOT=/workspace');
if (!defined('GRAV_CLI')) {
    define('GRAV_CLI', true);
}
chdir('/workspace');

require_once '/workspace/vendor/autoload.php';

spl_autoload_register(function (string $class): void {
    $prefix = 'CweTests\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }
    $relative = str_replace('\\', '/', substr($class, strlen($prefix)));
    $file = __DIR__ . '/src/' . $relative . '.php';
    if (is_file($file)) {
        require_once $file;
    }
});
