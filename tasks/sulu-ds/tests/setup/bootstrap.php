<?php

$loader = require '/workspace/vendor/autoload.php';

\spl_autoload_register(static function (string $class): void {
    $prefix = 'Sulu\\Task\\Harness\\';
    if (!\str_starts_with($class, $prefix)) {
        return;
    }

    $path = __DIR__ . '/../harness/' . \str_replace('\\', '/', \substr($class, \strlen($prefix))) . '.php';
    if (\is_file($path)) {
        require $path;
    }
});

return $loader;
