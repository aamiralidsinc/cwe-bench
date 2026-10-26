<?php

use Tiptap\Extensions\FontFamily;
use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\TextStyle;

return [
    'name' => 'font family style renders unchanged',
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
                        'attrs' => ['fontFamily' => 'Arial'],
                    ]],
                ]],
            ]],
        ];

        tiptap_check(
            tiptap_html($document, [new StarterKit, new FontFamily, new TextStyle])
                === '<p><span style="font-family: Arial;">Example</span></p>',
            'a valid font family stopped rendering'
        );
    },
];
