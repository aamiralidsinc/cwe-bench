<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\Link;
use Tiptap\Nodes\Image;

return [
    'name' => 'image source supplied as a list',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'image',
                'attrs' => [
                    'src' => ['ZqSrcOne', 'ZqSrcTwo'],
                    'alt' => 'a picture',
                ],
            ]],
        ];

        $html = tiptap_html($document, [new StarterKit, new Link, new Image]);

        tiptap_check(! str_contains($html, 'ZqSrc'), 'the non-string image source appeared in the output');
        tiptap_check(! preg_match('/\ssrc\s*=/', $html), 'the non-string image source produced a source attribute');
        tiptap_check(str_contains($html, '<img '), 'the image element was lost');
        tiptap_check(str_contains($html, 'alt="a picture"'), 'the valid image description was lost');
    },
];
