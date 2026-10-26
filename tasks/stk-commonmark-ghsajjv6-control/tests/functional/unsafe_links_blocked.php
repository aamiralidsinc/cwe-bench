<?php

declare(strict_types=1);

/*
 * Legitimate use of the product: the document below must keep converting to exactly the same
 * HTML as it does today.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\Attributes\AttributesExtension;
use League\CommonMark\Extension\GithubFlavoredMarkdownExtension;
use League\CommonMark\Extension\SmartPunct\SmartPunctExtension;

$markdown = <<<'GEN_MD'
[click me](javascript:alert(1)){href="javascript:alert(1)"}

GEN_MD;

$expected = <<<'GEN_HTML'
<p><a>click me</a></p>

GEN_HTML;

$extensions = [AttributesExtension::class, GithubFlavoredMarkdownExtension::class];
$config     = ['allow_unsafe_links' => false];

$actual = cm_converter($extensions, $config)->convert($markdown)->getContent();
cm_assert_same($expected, $actual, 'unsafe-links-blocked');
echo "ok\n";
