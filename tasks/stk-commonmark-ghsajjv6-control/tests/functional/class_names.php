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
{class="some-class(value)"}
Some text

{.some-class(value)}
Some text

{.-hello}
Some text

{.smile-😎 .some-class}
Some text

{id="smile-😎"}
Some text

{#smile-😎}
Some text

GEN_MD;

$expected = <<<'GEN_HTML'
<p class="some-class(value)">Some text</p>
<p class="some-class(value)">Some text</p>
<p class="-hello">Some text</p>
<p class="smile-😎 some-class">Some text</p>
<p id="smile-😎">Some text</p>
<p id="smile-😎">Some text</p>

GEN_HTML;

$extensions = [AttributesExtension::class, GithubFlavoredMarkdownExtension::class];
$config     = [];

$actual = cm_converter($extensions, $config)->convert($markdown)->getContent();
cm_assert_same($expected, $actual, 'class-names');
echo "ok\n";
