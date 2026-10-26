<?php

error_reporting(E_ALL & ~E_WARNING & ~E_NOTICE & ~E_DEPRECATED);

chdir('/workspace');

@mkdir('/tmp/librenms-htests-logs', 0777, true);

require_once '/workspace/vendor/autoload.php';
require_once '/workspace/includes/common.php';
require_once '/workspace/includes/dbFacile.php';
require_once '/workspace/includes/syslog.php';
require_once '/workspace/includes/snmp.inc.php';
require_once '/workspace/includes/services.inc.php';
require_once '/workspace/includes/functions.php';
require_once '/workspace/includes/rewrites.php';
require_once '/workspace/includes/html/functions.inc.php';
require_once '/workspace/includes/discovery/functions.inc.php';
require_once '/workspace/includes/polling/functions.inc.php';

spl_autoload_register(function (string $class): void {
    $prefix = 'Bench\\';
    if (! str_starts_with($class, $prefix)) {
        return;
    }

    $file = __DIR__ . '/harness/' . str_replace('\\', '/', substr($class, strlen($prefix))) . '.php';
    if (is_file($file)) {
        require $file;
    }
});
