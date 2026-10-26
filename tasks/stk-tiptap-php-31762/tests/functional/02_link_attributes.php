<?php

use Tiptap\Extensions\StarterKit;
use Tiptap\Marks\Link;

return [
    'name' => 'link attributes keep their existing behaviour',
    'run' => function () {
        $extensions = [new StarterKit, new Link];

        $rel = [
            'type' => 'doc',
            'content' => [[
                'type' => 'text',
                'text' => 'Example',
                'marks' => [[
                    'type' => 'link',
                    'attrs' => ['href' => 'https://tiptap.dev', 'rel' => 'noopener'],
                ]],
            ]],
        ];
        tiptap_check(
            tiptap_html($rel, $extensions)
                === '<a target="_blank" rel="noopener" href="https://tiptap.dev">Example</a>',
            'a valid link relation did not render as before'
        );

        $target = [
            'type' => 'doc',
            'content' => [[
                'type' => 'text',
                'text' => 'Example',
                'marks' => [[
                    'type' => 'link',
                    'attrs' => ['href' => 'https://tiptap.dev', 'target' => '_self'],
                ]],
            ]],
        ];
        tiptap_check(
            tiptap_html($target, $extensions)
                === '<a target="_self" rel="noopener noreferrer nofollow" href="https://tiptap.dev">Example</a>',
            'a valid link target did not render as before'
        );

        $nullTarget = [
            'type' => 'doc',
            'content' => [[
                'type' => 'text',
                'text' => 'Example',
                'marks' => [[
                    'type' => 'link',
                    'attrs' => ['href' => 'https://tiptap.dev', 'target' => null],
                ]],
            ]],
        ];
        tiptap_check(
            tiptap_html($nullTarget, $extensions)
                === '<a rel="noopener noreferrer nofollow" href="https://tiptap.dev">Example</a>',
            'a null attribute is no longer dropped'
        );

        $class = [
            'type' => 'doc',
            'content' => [[
                'type' => 'text',
                'text' => 'Example',
                'marks' => [[
                    'type' => 'link',
                    'attrs' => ['href' => 'https://tiptap.dev', 'class' => 'custom'],
                ]],
            ]],
        ];
        tiptap_check(
            tiptap_html($class, $extensions)
                === '<a target="_blank" rel="noopener noreferrer nofollow" href="https://tiptap.dev" class="custom">Example</a>',
            'a valid link class did not render as before'
        );
    },
];
