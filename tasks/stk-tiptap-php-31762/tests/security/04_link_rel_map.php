<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\Link;

return [
    'name' => 'link relation supplied as a map',
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
                        'rel' => ['ZqRelKey' => 'ZqRelValue'],
                    ],
                ]],
            ]],
        ];

        $html = tiptap_html($document, [new StarterKit, new Link]);

        tiptap_check(! str_contains($html, 'ZqRel'), 'the non-string relation appeared in the output');
        tiptap_check(str_contains($html, 'href="https://example.test/page"'), 'the valid link address was lost');
        tiptap_check(str_contains($html, '<a '), 'the link element was lost');
        tiptap_check(
            ! preg_match('/\srel\s*=/', $html) || str_contains($html, 'rel="noopener noreferrer nofollow"'),
            'the non-string relation was rendered instead of being omitted'
        );
    },
];
