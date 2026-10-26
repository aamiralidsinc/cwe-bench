<?php

return [
    'name' => 'a basic document renders as before',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'paragraph',
                'content' => [['type' => 'text', 'text' => 'Example Text']],
            ]],
        ];

        tiptap_check(
            tiptap_html($document) === '<p>Example Text</p>',
            'a basic document no longer renders as before'
        );
    },
];
