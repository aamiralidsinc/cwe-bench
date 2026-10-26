<?php
/**
 * Bootstrap for the hidden suites.
 *
 * The socket server classes normally load the platform's generated configuration, which opens a
 * database and a session. The verifier supplies a small configuration that provides the globals,
 * the platform helpers and the two platform classes the socket server asks for, and then loads
 * the platform's real function library (including the token encryption the server verifies with).
 * Nothing here imports or copies the socket server classes; every suite drives them directly.
 */
$appRoot = getenv('CWE_APP_ROOT');
if (!$appRoot) {
    $appRoot = '/workspace';
}
$appRoot = rtrim($appRoot, '/') . '/';
define('CWE_APP_ROOT', $appRoot);

if (!is_dir($appRoot . 'videos')) {
    @mkdir($appRoot . 'videos', 0775, true);
}

$configFile = $appRoot . 'videos/configuration.php';
$config = "<?php\n"
    . "// Written by the grading harness: a lightweight boot for the platform's socket server.\n"
    . "\$global = [];\n"
    . "\$global['systemRootPath'] = " . var_export($appRoot, true) . ";\n"
    . "\$global['webSiteRootURL'] = 'http://127.0.0.1:9/';\n"
    . "\$global['webSiteRootPath'] = '';\n"
    . "\$global['salt'] = 'socket-test-salt';\n"
    . "\$global['saltV2'] = 'socket-test-salt-v2';\n"
    . "\$global['skippPlugins'] = [];\n"
    . "\$global['logfile'] = '/tmp/avideo-socket-test.log';\n"
    . "\$global['noDebug'] = 1;\n"
    . "if (!class_exists('User')) {\n"
    . "    class User {\n"
    . "        public static function getId() { return 0; }\n"
    . "        public static function isAdmin() { return false; }\n"
    . "        public static function getNameIdentification() { return 'guest'; }\n"
    . "        public static function getNameIdentificationById(\$id) { return empty(\$id) ? 'guest' : ('user' . intval(\$id)); }\n"
    . "    }\n"
    . "}\n"
    . "if (!class_exists('AVideoPlugin')) {\n"
    . "    class AVideoPlugin {\n"
    . "        public static function isEnabledByName(\$name) { return false; }\n"
    . "        public static function getDataObject(\$name) { return new stdClass(); }\n"
    . "    }\n"
    . "}\n"
    . "require_once \$global['systemRootPath'] . 'objects/functions.php';\n"
    . "require_once \$global['systemRootPath'] . 'objects/Object.php';\n";
if (file_put_contents($configFile, $config) === false) {
    fwrite(STDERR, "bootstrap: cannot write $configFile\n");
    exit(1);
}

require $configFile;

require_once $appRoot . 'vendor/autoload.php';
// React's event loop auto-runs at shutdown once it is created; stop it now and again from the
// harness so a server that registers a periodic timer cannot keep the runner alive.
require_once __DIR__ . '/support/RatchetStubs.php';

if (class_exists('React\\EventLoop\\Loop')) {
    React\EventLoop\Loop::get();
    React\EventLoop\Loop::stop();
}

error_reporting(E_ERROR | E_PARSE);
ini_set('display_errors', '0');

require_once __DIR__ . '/support/ServerHarness.php';
