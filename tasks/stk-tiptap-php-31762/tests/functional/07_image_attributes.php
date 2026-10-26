<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Nodes\Image;

return [
    'name' => 'image attributes render unchanged',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'image',
                'attrs' => [
                    'src' => 'https://example.test/i.png',
                    'alt' => 'pic',
                    'title' => 'T',
                    'width' => 640,
                    'height' => 480,
                ],
            ]],
        ];

        tiptap_check(
            tiptap_html($document, [new StarterKit, new Image])
                === '<img src="https://example.test/i.png" alt="pic" title="T" width="640" height="480">',
            'valid image attributes stopped rendering'
        );
    },
];
