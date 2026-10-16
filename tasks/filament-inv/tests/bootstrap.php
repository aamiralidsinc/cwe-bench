<?php

// The verifier runs the hidden tests from /tests against the application in /app.
// We reuse the application's own autoloader and the framework's test bootstrap
// (which pre-generates a facade cache), then register a tiny PSR-4 autoloader for
// the CweTests\ namespace that holds this task's TestCase and fixtures.
require_once '/app/vendor/autoload.php';
require_once '/app/tests/bootstrap.php';

spl_autoload_register(function (string $class): void {
    $prefix = 'CweTests\\';

    if (! str_starts_with($class, $prefix)) {
        return;
    }

    $relative = str_replace('\\', '/', substr($class, strlen($prefix)));
    $file = __DIR__ . '/src/' . $relative . '.php';

    if (is_file($file)) {
        require_once $file;
    }
});
