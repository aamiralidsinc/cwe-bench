<?php

declare(strict_types=1);

/*
 * Smart punctuation: alternating unpaired double quotes and apostrophes after short text runs.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\SmartPunct\SmartPunctExtension;

ini_set('memory_limit', '1024M');

$n       = 90000;
$segment = str_repeat('a', 31);

$input    = str_repeat($segment . '" \' ', $n);
$expected = '<p>' . str_repeat($segment . "\u{201C} \u{2019} ", $n - 1) . $segment . "\u{201C} \u{2019}</p>\n";

$start   = microtime(true);
$actual  = cm_converter([SmartPunctExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'unpaired mixed quotes');
cm_assert_fast($elapsed, 20.0, 'unpaired mixed quotes');
echo "ok\n";
