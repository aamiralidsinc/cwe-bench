<?php

// The verifier runs the hidden tests from /tests against the application in /app.
// Reuse the application's own Composer autoloader, then register a tiny PSR-4
// autoloader for the CweTests\ namespace that holds this task's base TestCase.

require_once '/app/vendor/autoload.php';

if (!defined('GRAV_CLI')) {
    define('GRAV_CLI', true);
}
chdir('/app');

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
