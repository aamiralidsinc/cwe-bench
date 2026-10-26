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
Header 1            {#header1}
========

## Header 2 ##
{#header2}

## The Site    {.main}

## The Site ##
{.main .shine #the-site}

[link](url){#id1 .class1} ![img](url){#id2 .class2}
**bold**{.bold} paragraph
{#text}

this is just normal text {.main .shine #the-site}

some { brackets

some } brackets

some { } brackets

A link inside of an emphasis tag: *[link](http://url.com){target="_blank"}*.

Attributes without quote and non-whitespace char [link](http://url.com){target=_blank}

Attributes without quote and non-whitespace char and a dot [link](http://url.com){target=_blank}.

Multiple attributes without quote and non-whitespace char and a dot [link](http://url.com){#id .class target=_blank}.

![image](/assets/image.jpg){some-text}

![image](/assets/image.jpg){boolean-attribute="boolean-attribute"}

A paragraph containing {{ mustache }} templating

A paragraph ending with {{ mustache }} templating

{{ mustache }} A paragraph starting with mustache templating

a. [Some{text}](https://example.com).

b. [Some{.text}](https://example.com).

c. [Some](https://example.com){.text}.

d. [Some{text}](https://example.com).

e. [Some](https://example.com){text="text"}.

f. [Some](https://example.com){text=true}.

g. [Some{{text}}](https://example.com).

{hello="hello"}
some

{.test hello="hello"}
some

{hello="hello" .test}
some

{hello="hello" goodbye="goodbye"}
some

GEN_MD;

$expected = <<<'GEN_HTML'
<h1 id="header1">Header 1</h1>
<h2 id="header2">Header 2</h2>
<h2 class="main">The Site</h2>
<h2 class="main shine" id="the-site">The Site</h2>
<p id="text"><a class="class1" id="id1" href="url">link</a> <img class="class2" id="id2" src="url" alt="img" />
<strong class="bold">bold</strong> paragraph</p>
<p class="main shine" id="the-site">this is just normal text</p>
<p>some { brackets</p>
<p>some } brackets</p>
<p>some { } brackets</p>
<p>A link inside of an emphasis tag: <em><a target="_blank" href="http://url.com" rel="noopener noreferrer">link</a></em>.</p>
<p>Attributes without quote and non-whitespace char <a target="_blank" href="http://url.com" rel="noopener noreferrer">link</a></p>
<p>Attributes without quote and non-whitespace char and a dot <a target="_blank" href="http://url.com" rel="noopener noreferrer">link</a>.</p>
<p>Multiple attributes without quote and non-whitespace char and a dot <a class="class" id="id" target="_blank" href="http://url.com" rel="noopener noreferrer">link</a>.</p>
<p><img src="/assets/image.jpg" alt="image" />{some-text}</p>
<p><img boolean-attribute="boolean-attribute" src="/assets/image.jpg" alt="image" /></p>
<p>A paragraph containing {{ mustache }} templating</p>
<p>A paragraph ending with {{ mustache }} templating</p>
<p>{{ mustache }} A paragraph starting with mustache templating</p>
<p>a. <a href="https://example.com">Some{text}</a>.</p>
<p>b. <a href="https://example.com">Some</a>.</p>
<p>c. <a class="text" href="https://example.com">Some</a>.</p>
<p>d. <a href="https://example.com">Some{text}</a>.</p>
<p>e. <a text="text" href="https://example.com">Some</a>.</p>
<p>f. <a text href="https://example.com">Some</a>.</p>
<p>g. <a href="https://example.com">Some{{text}}</a>.</p>
<p hello="hello">some</p>
<p class="test" hello="hello">some</p>
<p class="test" hello="hello">some</p>
<p hello="hello" goodbye="goodbye">some</p>

GEN_HTML;

$extensions = [AttributesExtension::class, GithubFlavoredMarkdownExtension::class];
$config     = [];

$actual = cm_converter($extensions, $config)->convert($markdown)->getContent();
cm_assert_same($expected, $actual, 'special-attributes');
echo "ok\n";
