<?php
/**
 * Renders one CMS URL in a fresh PHP process.
 *
 * The compiled-template cache and the CMS object cache are per process, so a request that must
 * observe a template file changed on disk has to be served by a new process, exactly as a later
 * request would be.
 *
 * Usage: php render.php <app-root> <themes-root> <theme-name> <url>
 */

$root = isset($argv[1]) ? rtrim($argv[1], '/') : '';
$themesRoot = isset($argv[2]) ? $argv[2] : '';
$themeName = isset($argv[3]) ? $argv[3] : '';
$url = isset($argv[4]) ? $argv[4] : '/';

if ($root === '' || $themesRoot === '' || $themeName === '') {
    fwrite(STDERR, "usage: php render.php <app-root> <themes-root> <theme-name> <url>\n");
    exit(2);
}

require $root . '/bootstrap/autoload.php';

$loader = new October\Rain\Support\ClassLoader(
    new October\Rain\Filesystem\Filesystem,
    $root . '/',
    $root . '/storage/framework/classes.php'
);
$loader->register();
$loader->addDirectories(['modules', 'plugins']);

$app = require $root . '/bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

$app['cache']->setDefaultDriver('array');
\Config::set('cms.enableSafeMode', true);
\App::setThemesPath($themesRoot);

try {
    $theme = \Cms\Classes\Theme::load($themeName);
    $controller = new \Cms\Classes\Controller($theme);
    $result = $controller->run($url);
    $output = is_object($result) ? $result->getContent() : (string) $result;
    fwrite(STDOUT, $output);
}
catch (\Throwable $e) {
    fwrite(STDOUT, 'RENDER-ERROR ' . get_class($e) . ': ' . $e->getMessage());
}
