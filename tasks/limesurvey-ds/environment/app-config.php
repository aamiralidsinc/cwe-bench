<?php if (!defined('BASEPATH')) {
    exit('No direct script access allowed');
}
/*
 * Local development configuration for this container.
 * The database server is the MariaDB instance documented in the report;
 * the public URL is the address this installation publishes in emails.
 */
return array(
    'components' => array(
        'db' => array(
            'connectionString' => 'mysql:host=127.0.0.1;port=3307;dbname=limesurvey;',
            'emulatePrepare' => true,
            'username' => 'limesurvey',
            'password' => 'lspass',
            'charset' => 'utf8mb4',
            'tablePrefix' => 'lime_',
        ),
        'urlManager' => array(
            'urlFormat' => 'get',
            'rules' => array(),
            'showScriptName' => true,
        ),
    ),
    'config' => array(
        'debug' => 0,
        'debugsql' => 0,
        'publicurl' => 'https://trusted.example/limesurvey',
    ),
);
