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
* list item
* list item {.classA}
  {.classB}
{.classC}


{.classA}
*   {.classD}

    {.classB}
    {.classC} list item

    {#id1}
    Another paragraph

    {.classE}
*   list item


{.classA}
*   list item {.classB}
    {.classC}

*   list item {.classD}
    {.classE}

- {.lala} this li will get the class lala
- this one will get the class foo {.foo}
{.bar}

GEN_MD;

$expected = <<<'GEN_HTML'
<ul class="classC">
<li>list item</li>
<li class="classA classB">list item</li>
</ul>
<ul class="classA">
<li class="classD classE">
<p class="classB classC">list item</p>
<p id="id1">Another paragraph</p>
</li>
<li>
<p>list item</p>
</li>
</ul>
<ul class="classA">
<li>
<p class="classB classC">list item</p>
</li>
<li>
<p class="classD classE">list item</p>
</li>
</ul>
<ul class="bar">
<li class="lala">this li will get the class lala</li>
<li class="foo">this one will get the class foo</li>
</ul>

GEN_HTML;

$extensions = [AttributesExtension::class, GithubFlavoredMarkdownExtension::class];
$config     = [];

$actual = cm_converter($extensions, $config)->convert($markdown)->getContent();
cm_assert_same($expected, $actual, 'list-attributes');
echo "ok\n";
