<?php

define('TEST_DATA_DIR', '/workspace/.htests/_data');
define('TEST_OUTPUT_DIR', '/workspace/.htests/_output');
define('TEST_LOG_FILE', 'debug.log');

@\mkdir(TEST_OUTPUT_DIR, 0777, true);

require_once '/workspace/vendor/autoload.php';
require_once __DIR__ . '/setup-test-logger.php';

spl_autoload_register(function (string $class) : void {
    $prefix = 'CweTests\\';
    if (\strncmp($class, $prefix, \strlen($prefix)) !== 0) {
        return;
    }
    $relative = \str_replace('\\', '/', \substr($class, \strlen($prefix)));
    $file = __DIR__ . '/src/' . $relative . '.php';
    if (\is_file($file)) {
        require_once $file;
    }
});
