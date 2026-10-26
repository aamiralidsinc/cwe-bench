<?php

use Tiptap\Nodes\Paragraph;
use Tiptap\Nodes\Table;
use Tiptap\Nodes\TableCell;
use Tiptap\Nodes\TableHeader;
use Tiptap\Nodes\TableRow;
use Tiptap\Nodes\Text;

return [
    'name' => 'cell width supplied as a string',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'table',
                'content' => [[
                    'type' => 'tableRow',
                    'content' => [[
                        'type' => 'tableCell',
                        'attrs' => [
                            'colwidth' => 'ZqWidthOne,ZqWidthTwo',
                            'colspan' => 2,
                        ],
                        'content' => [[
                            'type' => 'paragraph',
                            'content' => [['type' => 'text', 'text' => 'cell']],
                        ]],
                    ]],
                ]],
            ]],
        ];

        $html = tiptap_html($document, [new Table, new TableRow, new TableCell, new TableHeader, new Paragraph, new Text]);

        tiptap_check(! str_contains($html, 'ZqWidth'), 'the non-list cell width appeared in the output');
        tiptap_check(! preg_match('/\sdata-colwidth\s*=/', $html), 'the non-list cell width produced a width attribute');
        tiptap_check(str_contains($html, 'colspan="2"'), 'the valid cell span was lost');
        tiptap_check(str_contains($html, 'cell'), 'the cell text was lost');
    },
];
