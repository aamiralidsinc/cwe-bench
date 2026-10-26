<?php

use Tiptap\Extensions\Color;
use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\TextStyle;

return [
    'name' => 'colour style renders unchanged',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'paragraph',
                'content' => [[
                    'type' => 'text',
                    'text' => 'Example',
                    'marks' => [[
                        'type' => 'textStyle',
                        'attrs' => ['color' => 'red'],
                    ]],
                ]],
            ]],
        ];

        tiptap_check(
            tiptap_html($document, [new StarterKit, new Color, new TextStyle])
                === '<p><span style="color: red;">Example</span></p>',
            'a valid colour style stopped rendering'
        );
    },
];
