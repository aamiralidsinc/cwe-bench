<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\Link;
use Tiptap\Nodes\Image;

return [
    'name' => 'image description supplied as a map',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'image',
                'attrs' => [
                    'src' => 'https://example.test/i.png',
                    'alt' => ['ZqAltKey' => 'ZqAltValue'],
                ],
            ]],
        ];

        $html = tiptap_html($document, [new StarterKit, new Link, new Image]);

        tiptap_check(! str_contains($html, 'ZqAlt'), 'the non-string image description appeared in the output');
        tiptap_check(! preg_match('/\salt\s*=/', $html), 'the non-string image description produced a description attribute');
        tiptap_check(str_contains($html, '<img '), 'the image element was lost');
        tiptap_check(str_contains($html, 'src="https://example.test/i.png"'), 'the valid image source was lost');
    },
];
