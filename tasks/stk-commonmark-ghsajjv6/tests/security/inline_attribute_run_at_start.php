<?php

declare(strict_types=1);

/*
 * Attributes: a long run of inline attribute blocks at the start of a block. Each one applies to
 * the surrounding block; the document must still convert quickly and the attributes must land.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\Attributes\AttributesExtension;

ini_set('memory_limit', '1024M');

$n = 36000;

$input    = str_repeat('{#a}', $n);
$expected = '<p id="a"></p>' . "\n";

$start   = microtime(true);
$actual  = cm_converter([AttributesExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'inline attribute run at start of block');
cm_assert_fast($elapsed, 20.0, 'inline attribute run at start of block');
echo "ok\n";
