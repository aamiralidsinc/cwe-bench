<?php

declare(strict_types=1);

/*
 * Attributes: a long run of inline attributes with distinct names applying to one element.
 * Every attribute must be rendered and the document must convert quickly.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\Attributes\AttributesExtension;

ini_set('memory_limit', '1024M');

$n = 48000;

$parts = [];
for ($i = 0; $i < $n; $i++) {
    $parts[] = '{k' . $i . '="' . $i . '"}';
}

$input    = '*x*' . implode('', $parts);
$expected = '<p><em ' . implode(' ', array_map(static fn (int $i): string => 'k' . $i . '="' . $i . '"', range(0, $n - 1))) . '>x</em></p>' . "\n";

$start   = microtime(true);
$actual  = cm_converter([AttributesExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'inline named attribute run');
cm_assert_fast($elapsed, 20.0, 'inline named attribute run');
echo "ok\n";
