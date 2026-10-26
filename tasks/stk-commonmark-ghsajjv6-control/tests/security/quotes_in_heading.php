<?php

declare(strict_types=1);

/*
 * Smart punctuation: a long run of unpaired quotes inside a heading.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\SmartPunct\SmartPunctExtension;

ini_set('memory_limit', '1024M');

$n       = 56000;
$segment = str_repeat('a', 63);

$input    = '# ' . str_repeat($segment . '" ', $n);
$expected = '<h1>' . str_repeat($segment . "\u{201C} ", $n - 1) . $segment . "\u{201C}</h1>\n";

$start   = microtime(true);
$actual  = cm_converter([SmartPunctExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'unpaired quotes inside a heading');
cm_assert_fast($elapsed, 20.0, 'unpaired quotes inside a heading');
echo "ok\n";
