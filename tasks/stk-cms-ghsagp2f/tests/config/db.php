<?php
/**
 * The harness database. test.sh creates it on the local MariaDB instance and it never
 * leaves the verifier container.
 */
return [
    'driver' => 'mysql',
    'dsn' => 'mysql:host=127.0.0.1;port=3306;dbname=craft_test',
    'server' => '127.0.0.1',
    'port' => 3306,
    'database' => 'craft_test',
    'user' => 'craft',
    'password' => 'craftpass',
    'schema' => '',
    'tablePrefix' => '',
    'charset' => 'utf8mb4',
    'collation' => 'utf8mb4_unicode_ci',
];
