<?php

declare(strict_types=1);

/*
 * Hidden-test bootstrap. The suites are copied to <root>/.htests at grading time; the product
 * source is the restored <root>/src, and the runtime dependencies ship in <root>/.htests/vendor.
 */

$root = \dirname(__DIR__);

require $root . '/.htests/vendor/autoload.php';

spl_autoload_register(static function (string $class) use ($root): void {
    $prefix = 'League\\CommonMark\\';
    if (strncmp($class, $prefix, \strlen($prefix)) !== 0) {
        return;
    }

    $file = $root . '/src/' . \str_replace('\\', '/', \substr($class, \strlen($prefix))) . '.php';
    if (\is_file($file)) {
        require $file;
    }
});

/**
 * Build the public converter with the requested first-party extensions.
 *
 * @param list<class-string>   $extensions
 * @param array<string, mixed> $config
 */
function cm_converter(array $extensions, array $config = []): \League\CommonMark\MarkdownConverter
{
    $environment = new \League\CommonMark\Environment\Environment($config);
    $environment->addExtension(new \League\CommonMark\Extension\CommonMark\CommonMarkCoreExtension());
    foreach ($extensions as $extension) {
        $environment->addExtension(new $extension());
    }

    return new \League\CommonMark\MarkdownConverter($environment);
}

/**
 * Fail the test (exit 1) if the conversion output is not exactly the expected HTML.
 */
function cm_assert_same(string $expected, string $actual, string $label): void
{
    if ($actual !== $expected) {
        $at = 0;
        $limit = \min(\strlen($actual), \strlen($expected));
        while ($at < $limit && $actual[$at] === $expected[$at]) {
            $at++;
        }

        \fwrite(STDERR, \sprintf(
            "%s: output mismatch at byte %d (expected %d bytes, got %d)\n expected: %s\n actual:   %s\n",
            $label,
            $at,
            \strlen($expected),
            \strlen($actual),
            \var_export(\substr($expected, \max(0, $at - 40), 120), true),
            \var_export(\substr($actual, \max(0, $at - 40), 120), true)
        ));
        exit(1);
    }
}

/**
 * Convert a document and fail the test if the output is not exactly the expected HTML.
 */
function cm_assert_output(string $expected, string $input, array $extensions, string $label = ''): void
{
    $actual = cm_converter($extensions)->convert($input)->getContent();
    cm_assert_same($expected, $actual, $label !== '' ? $label : 'conversion');
}

/**
 * Assert that a conversion finishes within a wall-clock bound.
 */
function cm_assert_fast(float $seconds, float $limit, string $label): void
{
    if ($seconds > $limit) {
        \fwrite(STDERR, \sprintf("%s: conversion took %.2fs, limit %.2fs\n", $label, $seconds, $limit));
        exit(1);
    }
}
