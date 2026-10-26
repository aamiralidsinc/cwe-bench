<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\Link;

return [
    'name' => 'valid link addresses render unchanged',
    'run' => function () {
        $cases = [
            'https://tiptap.dev',
            '/relative/path',
            '//cdn.example.test/x',
            'mailto:someone@example.test',
            'ftp://files.example.test/pub',
        ];

        foreach ($cases as $address) {
            $document = [
                'type' => 'doc',
                'content' => [[
                    'type' => 'text',
                    'text' => 'Example',
                    'marks' => [[
                        'type' => 'link',
                        'attrs' => ['href' => $address],
                    ]],
                ]],
            ];

            $expected = '<a target="_blank" rel="noopener noreferrer nofollow" href="'
                . $address . '">Example</a>';

            tiptap_check(
                tiptap_html($document, [new StarterKit, new Link]) === $expected,
                'a valid link address did not render as before: ' . $address
            );
        }
    },
];
