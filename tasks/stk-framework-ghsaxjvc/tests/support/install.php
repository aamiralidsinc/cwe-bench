<?php
/**
 * Verifier setup: installs Flarum into a local test site backed by the MariaDB service that
 * test.sh started. Runs as the unprivileged agent user.
 */

require '/workspace/framework/core/vendor/autoload.php';

use Flarum\Foundation\Paths;
use Flarum\Install\AdminUser;
use Flarum\Install\BaseUrl;
use Flarum\Install\DatabaseConfig;
use Flarum\Install\Installation;

$base = '/workspace/.htests/site';

foreach (['', '/public', '/public/assets', '/storage', '/storage/formatter', '/storage/sessions',
             '/storage/views', '/vendor', '/vendor/composer'] as $dir) {
    if (! is_dir($base . $dir) && ! @mkdir($base . $dir, 0777, true) && ! is_dir($base . $dir)) {
        fwrite(STDERR, "cannot create {$base}{$dir}\n");
        exit(1);
    }
}

if (! is_file($base . '/vendor/composer/installed.json')) {
    file_put_contents($base . '/vendor/composer/installed.json', '{}');
}

$database = new DatabaseConfig('mysql', '127.0.0.1', 3306, 'flarum_test', 'flarum', 'flarumpass', '');

$installation = (new Installation(new Paths([
    'base' => $base,
    'public' => $base . '/public',
    'storage' => $base . '/storage',
    'vendor' => '/workspace/framework/core/vendor',
])))
    ->configPath('config.php')
    ->debugMode(true)
    ->baseUrl(BaseUrl::fromString('http://localhost/'))
    ->databaseConfig($database)
    ->adminUser(new AdminUser('admin', 'password', 'admin@machine.local'))
    ->settings(['mail_driver' => 'log'])
    ->extensions([])
    ->build();

$installation->run();

echo "installed\n";
