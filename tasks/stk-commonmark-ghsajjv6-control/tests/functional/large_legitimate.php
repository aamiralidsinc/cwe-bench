<?php

declare(strict_types=1);

/*
 * Legitimate use of the product: one element carries many class attributes (with repeats) and
 * many named attributes. The rendered attribute list must keep its order and its duplicates.
 */

require __DIR__ . '/../bootstrap.php';

use League\CommonMark\Extension\Attributes\AttributesExtension;

ini_set('memory_limit', '1024M');

$n       = 200;
$classes = [];
$named   = [];
for ($i = 0; $i < $n; $i++) {
    $classes[] = 'c' . $i;
    $named[]   = '{k' . $i . '="' . $i . '"}';
}

// Repeat the class list so the same class appears more than once, in order.
$inline = '';
foreach ([$classes, $classes] as $list) {
    foreach ($list as $class) {
        $inline .= '{.' . $class . '}';
    }
}
foreach ($named as $attribute) {
    $inline .= $attribute;
}

$markdown = '*x*' . $inline;
$expected = '<p><em class="' . implode(' ', array_merge($classes, $classes)) . '" '
    . implode(' ', array_map(static fn (int $i): string => 'k' . $i . '="' . $i . '"', range(0, $n - 1)))
    . '>x</em></p>' . "\n";

cm_assert_output($expected, $markdown, [AttributesExtension::class], 'large legitimate attribute document');
echo "ok\n";
