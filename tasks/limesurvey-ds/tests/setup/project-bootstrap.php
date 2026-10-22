<?php
/* Minimal bootstrap for running the project's own unit tests without the
 * browser-test base classes (the web-driver dev dependency is not installed). */
ob_start();
define('BASEPATH', '/workspace/vendor/yiisoft/yii/framework/');
define('EXT', '.php');
define('SELF', 'index-test.php');
define('ROOT', '/workspace');
define('FCPATH', '/workspace/');
define('SYSDIR', 'framework');
define('APPPATH', '/workspace/application/');
error_reporting(E_ALL & ~E_NOTICE & ~E_DEPRECATED);
require_once '/workspace/vendor/autoload.php';
require_once BASEPATH . 'yii.php';
require_once APPPATH . 'core/LSYii_Application.php';
$config = require APPPATH . 'config/internal.php';
$_SERVER['SCRIPT_FILENAME'] = 'index-test.php';
$_SERVER['SCRIPT_NAME'] = '/index-test.php';
$_SERVER['REQUEST_URI'] = 'index-test.php';
Yii::$enableIncludePath = false;
Yii::createApplication('LSYii_Application', $config);
require_once '/workspace/tests/TestHelper.php';
require_once '/workspace/tests/TestBaseClass.php';
restore_error_handler();
$_SERVER['SERVER_NAME'] = 'localhost';
$_SERVER['HTTP_HOST'] = '';
$_SERVER['SERVER_PORT'] = 80;
$_SERVER['REQUEST_METHOD'] = 'GET';
