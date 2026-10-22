<?php
/* Build-time helper: create a demo participant table and a small demo data set
 * in the pre-installed database, so the container can be run and explored. */
define('BASEPATH', '.');
define('EXT', '.php');
require '/workspace/vendor/autoload.php';
require '/workspace/vendor/yiisoft/yii/framework/yii.php';
$sCurrentDir = '/workspace/application/commands';
$settings = require('/workspace/application/config/config-defaults.php');
$config = require('/workspace/application/config/internal.php');
$config['components']['session']['class'] = 'ConsoleHttpSession';
$config['components']['session']['cookieMode'] = 'none';
$config['components']['session']['cookieParams'] = [];
if (isset($config['config'])) {
    $settings = array_merge($settings, $config['config']);
}
unset($config['defaultController']);
unset($config['config']);
$config['runtimePath'] = '/workspace/tmp/runtime';
require '/workspace/application/core/ConsoleApplication.php';
$app = Yii::createApplication('ConsoleApplication', $config);
define('APPPATH', Yii::app()->getBasePath() . DIRECTORY_SEPARATOR);
Yii::import('application.helpers.ClassFactory');
ClassFactory::registerClass('Token_', 'Token');
ClassFactory::registerClass('Response_', 'Response');
$sid = (int) $argv[1];
Token::createTable($sid);
$db = Yii::app()->db;
$db->createCommand()->insert('{{tokens_' . $sid . '}}', [
    'firstname' => 'Demo',
    'lastname' => 'Participant',
    'email' => 'participant@example.org',
    'emailstatus' => 'OK',
    'token' => 'DEMOTOKEN001',
    'language' => 'en',
    'sent' => 'N',
    'remindersent' => 'N',
    'remindercount' => 0,
    'completed' => 'N',
    'usesleft' => 1,
]);
$db->createCommand()->update(
    '{{surveys}}',
    ['allowregister' => 'Y', 'allowsave' => 'Y', 'usetokens' => 'Y'],
    'sid=:sid',
    [':sid' => $sid]
);
echo "demo data ready\n";
