<?php

declare(strict_types=1);

// The hidden suites are copied into the project tree at grading time and run
// from there against the restored project. They use the project's own
// autoloader and its functional-test bootstrap, plus a small autoloader for the
// CweTests\ support classes that live next to this file.

$projectRoot = dirname(__DIR__);

require_once $projectRoot . '/vendor/autoload.php';

spl_autoload_register(static function (string $class) use ($projectRoot): void {
    $prefix = 'CweTests\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }
    $relative = str_replace('\\', '/', substr($class, strlen($prefix)));
    $candidates = [
        __DIR__ . '/support/' . $relative . '.php',
        __DIR__ . '/support/Fixtures/' . $relative . '.php',
    ];
    foreach ($candidates as $file) {
        if (is_file($file)) {
            require_once $file;
            return;
        }
    }
}, true, true);

require_once $projectRoot . '/Build/phpunit/FunctionalTestsBootstrap.php';
