<?php
/**
 * Load the project under test from the restored workspace by PSR-4. The hidden suites only need
 * the classes in src/, so no dependency tree or installed autoloader is required.
 */
$root = getenv('TIPTAP_ROOT');
if (! is_string($root) || $root === '') {
    $root = '/workspace';
}
$root = rtrim($root, '/');

spl_autoload_register(function ($class) use ($root) {
    $prefix = 'Tiptap\\';

    if (strncmp($class, $prefix, strlen($prefix)) !== 0) {
        return;
    }

    $relative = str_replace('\\', '/', substr($class, strlen($prefix)));
    $file = $root . '/src/' . $relative . '.php';

    if (is_file($file)) {
        require $file;
    }
});
