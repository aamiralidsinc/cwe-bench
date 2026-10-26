<?php

use Tiptap\Nodes\Paragraph;
use Tiptap\Nodes\Table;
use Tiptap\Nodes\TableCell;
use Tiptap\Nodes\TableHeader;
use Tiptap\Nodes\TableRow;
use Tiptap\Nodes\Text;

return [
    'name' => 'table cells render their numeric and list values',
    'run' => function () {
        $document = [
            'type' => 'doc',
            'content' => [[
                'type' => 'table',
                'content' => [
                    [
                        'type' => 'tableRow',
                        'content' => [
                            [
                                'type' => 'tableHeader',
                                'attrs' => ['colspan' => 2, 'colwidth' => [100, 0]],
                                'content' => [[
                                    'type' => 'paragraph',
                                    'content' => [['type' => 'text', 'text' => 'h']],
                                ]],
                            ],
                            [
                                'type' => 'tableCell',
                                'attrs' => ['rowspan' => 2],
                                'content' => [[
                                    'type' => 'paragraph',
                                    'content' => [['type' => 'text', 'text' => 'a']],
                                ]],
                            ],
                        ],
                    ],
                    [
                        'type' => 'tableRow',
                        'content' => [[
                            'type' => 'tableCell',
                            'attrs' => ['colwidth' => ['100', '0']],
                            'content' => [[
                                'type' => 'paragraph',
                                'content' => [['type' => 'text', 'text' => 'b']],
                            ]],
                        ]],
                    ],
                ],
            ]],
        ];

        $expected = '<table><tbody><tr>'
            . '<th colspan="2" data-colwidth="100,0"><p>h</p></th>'
            . '<td rowspan="2"><p>a</p></td>'
            . '</tr><tr>'
            . '<td data-colwidth="100,0"><p>b</p></td>'
            . '</tr></tbody></table>';

        $extensions = [new Table, new TableRow, new TableCell, new TableHeader, new Paragraph, new Text];

        tiptap_check(
            tiptap_html($document, $extensions) === $expected,
            'numeric spans or list widths stopped rendering'
        );
    },
];
