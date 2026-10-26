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
""You miss 100% of the shots you don't take" - Wayne Gretzky" -- Michael Scott

... or so the quote goes

GEN_MD;

$expected = <<<'GEN_HTML'
<p>““You miss 100% of the shots you don’t take” - Wayne Gretzky” – Michael Scott</p>
<p>… or so the quote goes</p>

GEN_HTML;

$extensions = [SmartPunctExtension::class];
$config     = [];

$actual = cm_converter($extensions, $config)->convert($markdown)->getContent();
cm_assert_same($expected, $actual, 'smartpunct-pairs');
echo "ok\n";
