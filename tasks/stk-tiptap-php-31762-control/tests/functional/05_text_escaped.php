<?php

return [
    'name' => 'string text is escaped as before',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'text',
                'text' => '<script>alert(1)</script>',
            ]],
        ];

        tiptap_check(
            tiptap_html($document) === '&lt;script&gt;alert(1)&lt;/script&gt;',
            'string text is no longer escaped as before'
        );
    },
];
