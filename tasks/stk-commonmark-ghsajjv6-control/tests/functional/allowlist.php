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
Header with attributes {#header1}
---------------------------------

{class="text" hello="world"}
some text

![image](/assets/image.jpg){align=left width=100px}

GEN_MD;

$expected = <<<'GEN_HTML'
<h2 id="header1">Header with attributes</h2>
<p class="text">some text</p>
<p><img align="left" src="/assets/image.jpg" alt="image" /></p>

GEN_HTML;

$extensions = [AttributesExtension::class, GithubFlavoredMarkdownExtension::class];
$config     = ['attributes' => ['allow' => ['id', 'class', 'align']]];

$actual = cm_converter($extensions, $config)->convert($markdown)->getContent();
cm_assert_same($expected, $actual, 'allowlist');
echo "ok\n";
