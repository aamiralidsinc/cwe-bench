<?php
/**
 * The harness never connects to a database; the application boots uninstalled and every test
 * stubs the service it needs. The array is present because the application's config service
 * reads it while building the component configuration.
 */
return [
    'dsn' => 'mysql:host=127.0.0.1;port=3306;dbname=craft_task_test',
    'driver' => 'mysql',
    'server' => '127.0.0.1',
    'port' => 3306,
    'database' => 'craft_task_test',
    'user' => 'craft',
    'password' => 'craft',
    'schema' => '',
    'tablePrefix' => '',
    'charset' => 'utf8mb4',
    'collation' => 'utf8mb4_unicode_ci',
];
