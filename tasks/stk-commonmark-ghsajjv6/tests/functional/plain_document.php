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
# Title

A normal paragraph with *emphasis* and a [link](/somewhere).

- one
- two
- three

> quoted text

GEN_MD;

$expected = <<<'GEN_HTML'
<h1>Title</h1>
<p>A normal paragraph with <em>emphasis</em> and a <a href="/somewhere">link</a>.</p>
<ul>
<li>one</li>
<li>two</li>
<li>three</li>
</ul>
<blockquote>
<p>quoted text</p>
</blockquote>

GEN_HTML;

$extensions = [];
$config     = [];

$actual = cm_converter($extensions, $config)->convert($markdown)->getContent();
cm_assert_same($expected, $actual, 'plain-document');
echo "ok\n";
