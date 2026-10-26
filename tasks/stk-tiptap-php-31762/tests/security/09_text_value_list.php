<?php

return [
    'name' => 'text value supplied as a list',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'paragraph',
                'content' => [
                    ['type' => 'text', 'text' => ['ZqTextOne', 'ZqTextTwo']],
                    ['type' => 'text', 'text' => 'safe'],
                ],
            ]],
        ];

        $html = tiptap_html($document);

        tiptap_check(! str_contains($html, 'ZqText'), 'the non-string text appeared in the output');
        tiptap_check($html === '<p>safe</p>', 'the remaining text did not render as it does for a valid document');
    },
];
