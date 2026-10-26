<?php

declare(strict_types=1);

/*
 * Attributes: a long contiguous run of block-level attribute blocks, each targeting the following
 * node. The reference definitions keep the run contiguous while leaving no node in the chain.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\Attributes\AttributesExtension;

ini_set('memory_limit', '1024M');

$n = 24000;

$input    = str_repeat("{#a}\n[a]: u\n", $n) . 'para';
$expected = '<p id="a">para</p>' . "\n";

$start   = microtime(true);
$actual  = cm_converter([AttributesExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'contiguous block attribute run');
cm_assert_fast($elapsed, 20.0, 'contiguous block attribute run');
echo "ok\n";
