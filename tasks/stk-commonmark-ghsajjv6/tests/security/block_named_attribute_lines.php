<?php

declare(strict_types=1);

/*
 * Attributes: many consecutive attribute lines with distinct names forming one attribute block.
 * Every attribute must be rendered and the document must convert quickly.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\Attributes\AttributesExtension;

ini_set('memory_limit', '1024M');

$n = 160000;

$parts = [];
for ($i = 0; $i < $n; $i++) {
    $parts[] = '{k' . $i . '="' . $i . "\"}\n";
}

$input    = implode('', $parts) . 'para';
$expected = '<p ' . implode(' ', array_map(static fn (int $i): string => 'k' . $i . '="' . $i . '"', range(0, $n - 1))) . '>para</p>' . "\n";

$start   = microtime(true);
$actual  = cm_converter([AttributesExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'attribute block named attribute lines');
cm_assert_fast($elapsed, 20.0, 'attribute block named attribute lines');
echo "ok\n";
