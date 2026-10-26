<?php

return [
    'name' => 'ordered list start value renders',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'orderedList',
                'attrs' => ['start' => 3],
                'content' => [[
                    'type' => 'listItem',
                    'content' => [['type' => 'text', 'text' => 'first list item']],
                ]],
            ]],
        ];

        tiptap_check(
            tiptap_html($document) === '<ol start="3"><li>first list item</li></ol>',
            'a numeric list start stopped rendering'
        );
    },
];
