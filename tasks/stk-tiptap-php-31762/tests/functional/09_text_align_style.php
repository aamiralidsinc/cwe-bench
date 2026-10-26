<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Extensions\TextAlign;

return [
    'name' => 'text alignment style renders unchanged',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'paragraph',
                'attrs' => ['textAlign' => 'center'],
                'content' => [['type' => 'text', 'text' => 'hi']],
            ]],
        ];

        tiptap_check(
            tiptap_html($document, [new StarterKit, new TextAlign(['types' => ['paragraph']])])
                === '<p style="text-align: center;">hi</p>',
            'a valid alignment style stopped rendering'
        );
    },
];
