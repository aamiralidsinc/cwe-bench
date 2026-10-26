<?php

declare(strict_types=1);

/*
 * Smart punctuation: a long run of text segments each followed by an unpaired double quote.
 * Every quote must still be converted and the whole document must convert quickly.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\SmartPunct\SmartPunctExtension;

ini_set('memory_limit', '1024M');

$n       = 64000;
$segment = str_repeat('a', 63);

$input    = str_repeat($segment . '" ', $n);
$expected = '<p>' . str_repeat($segment . "\u{201C} ", $n - 1) . $segment . "\u{201C}</p>\n";

$start   = microtime(true);
$actual  = cm_converter([SmartPunctExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'unpaired double quotes');
cm_assert_fast($elapsed, 20.0, 'unpaired double quotes');
echo "ok\n";
