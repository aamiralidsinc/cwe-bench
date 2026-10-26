<?php

declare(strict_types=1);

/*
 * Attributes: a long run of inline class attributes applying to one element. The rendered class
 * list must keep every class in order and the document must convert quickly.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\Attributes\AttributesExtension;

ini_set('memory_limit', '1024M');

$n = 60000;

$input    = '*x*' . str_repeat('{.c}', $n);
$expected = '<p><em class="' . rtrim(str_repeat('c ', $n)) . '">x</em></p>' . "\n";

$start   = microtime(true);
$actual  = cm_converter([AttributesExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'inline class run');
cm_assert_fast($elapsed, 20.0, 'inline class run');
echo "ok\n";
