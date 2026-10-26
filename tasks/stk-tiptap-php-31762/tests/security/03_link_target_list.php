<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\Link;

return [
    'name' => 'link target supplied as a list',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'text',
                'text' => 'Example',
                'marks' => [[
                    'type' => 'link',
                    'attrs' => [
                        'href' => 'https://example.test/page',
                        'target' => ['ZqTargetOne'],
                    ],
                ]],
            ]],
        ];

        $html = tiptap_html($document, [new StarterKit, new Link]);

        tiptap_check(! str_contains($html, 'ZqTarget'), 'the non-string target appeared in the output');
        tiptap_check(str_contains($html, 'href="https://example.test/page"'), 'the valid link address was lost');
        tiptap_check(str_contains($html, '<a '), 'the link element was lost');
        tiptap_check(
            ! preg_match('/\starget\s*=/', $html) || str_contains($html, 'target="_blank"'),
            'the non-string target was rendered instead of being omitted'
        );
    },
];
