<?php

declare(strict_types=1);

/*
 * Attributes: many consecutive class-attribute lines forming one attribute block.
 * The class list must keep every entry in order and the document must convert quickly.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\Attributes\AttributesExtension;

ini_set('memory_limit', '1024M');

$n = 60000;

$input    = str_repeat("{.c}\n", $n) . 'para';
$expected = '<p class="' . rtrim(str_repeat('c ', $n)) . '">para</p>' . "\n";

$start   = microtime(true);
$actual  = cm_converter([AttributesExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'attribute block class lines');
cm_assert_fast($elapsed, 20.0, 'attribute block class lines');
echo "ok\n";
