<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\Highlight;

return [
    'name' => 'highlight colour renders unchanged',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'paragraph',
                'content' => [[
                    'type' => 'text',
                    'text' => 'x',
                    'marks' => [[
                        'type' => 'highlight',
                        'attrs' => ['color' => 'yellow'],
                    ]],
                ]],
            ]],
        ];

        tiptap_check(
            tiptap_html($document, [new StarterKit, new Highlight(['multicolor' => true])])
                === '<p><mark data-color="yellow" style="background-color: yellow;">x</mark></p>',
            'a valid highlight colour stopped rendering'
        );
    },
];
