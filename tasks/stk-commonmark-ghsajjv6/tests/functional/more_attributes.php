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
{#par1}
Paragraph with a.

Header with attributes {#header1}
----------------------

### Header with attributes ### {#header2}

### Header no attributes ###

{#par1}
{.first}
{.second}Paragraph with a. {.third}
{.fourth}
{.fifth}

Paragraph with *emphasis*{.chello}
   {#par2}

{#invalid} [Invalid](example.com)

GEN_MD;

$expected = <<<'GEN_HTML'
<p id="par1">Paragraph with a.</p>
<h2 id="header1">Header with attributes</h2>
<h3 id="header2">Header with attributes ###</h3>
<h3>Header no attributes</h3>
<p class="first second third fourth fifth" id="par1">Paragraph with a.</p>
<p id="par2">Paragraph with <em class="chello">emphasis</em></p>
<p id="invalid"><a href="example.com">Invalid</a></p>

GEN_HTML;

$extensions = [AttributesExtension::class, GithubFlavoredMarkdownExtension::class];
$config     = [];

$actual = cm_converter($extensions, $config)->convert($markdown)->getContent();
cm_assert_same($expected, $actual, 'more-attributes');
echo "ok\n";
