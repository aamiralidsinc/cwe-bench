<?php

return [
    'name' => 'plain-text rendering of a map value',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'paragraph',
                'content' => [
                    ['type' => 'text', 'text' => ['ZqPlainKey' => 'ZqPlainValue']],
                    ['type' => 'text', 'text' => 'safe'],
                ],
            ]],
        ];

        $text = tiptap_text($document);

        tiptap_check(! str_contains($text, 'ZqPlain'), 'the non-string text appeared in the plain-text output');
        tiptap_check(trim($text) === 'safe', 'the remaining text did not render as it does for a valid document');
    },
];
