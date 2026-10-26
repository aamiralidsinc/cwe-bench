<?php

return [
    'name' => 'plain-text rendering keeps its behaviour',
    'run' => function () {
        tiptap_check(
            tiptap_text('<h1>Heading</h1><p>Paragraph</p>') === "Heading\n\nParagraph",
            'plain-text rendering changed'
        );

        tiptap_check(
            tiptap_text('<h1>Heading</h1><p>Paragraph</p>', null, ['blockSeparator' => "\n"])
                === "Heading\nParagraph",
            'the configurable block separator changed'
        );

        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'text',
                'text' => '<b>hi</b>',
            ]],
        ];

        tiptap_check(
            tiptap_text($document) === '&lt;b&gt;hi&lt;/b&gt;',
            'string text is no longer escaped in plain-text output'
        );
    },
];
