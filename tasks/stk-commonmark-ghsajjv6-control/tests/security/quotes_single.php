<?php

declare(strict_types=1);

/*
 * Smart punctuation: a long run of text segments each followed by an unpaired apostrophe.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\SmartPunct\SmartPunctExtension;

ini_set('memory_limit', '1024M');

$n       = 64000;
$segment = str_repeat('a', 63);

$input    = str_repeat($segment . "' ", $n);
$expected = '<p>' . str_repeat($segment . "\u{2019} ", $n - 1) . $segment . "\u{2019}</p>\n";

$start   = microtime(true);
$actual  = cm_converter([SmartPunctExtension::class])->convert($input)->getContent();
$elapsed = microtime(true) - $start;

cm_assert_same($expected, $actual, 'unpaired apostrophes');
cm_assert_fast($elapsed, 20.0, 'unpaired apostrophes');
echo "ok\n";
