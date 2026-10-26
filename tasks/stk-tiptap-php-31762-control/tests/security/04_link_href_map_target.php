<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\Link;

return [
    'name' => 'link address map beside a valid target',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'text',
                'text' => 'Example',
                'marks' => [[
                    'type' => 'link',
                    'attrs' => [
                        'href' => ['ZqAddrFive' => 'ZqAddrSix'],
                        'target' => '_self',
                    ],
                ]],
            ]],
        ];

        $html = tiptap_html($document, [new StarterKit, new Link]);

        tiptap_check(! str_contains($html, 'ZqAddr'), 'the non-string link address appeared in the output');
        tiptap_check(! preg_match('/\shref\s*=/', $html), 'the non-string link address produced an address attribute');
        tiptap_check(str_contains($html, 'target="_self"'), 'the valid target was lost');
        tiptap_check(str_contains($html, 'Example'), 'the link text was lost');
    },
];
