<?php
/**
 * Shared helpers for the hidden suites. Expected values always live in the test case itself;
 * these helpers only drive the product's public API.
 */
require_once __DIR__ . '/bootstrap.php';

/** Fail the current case with a message. */
function tiptap_check($condition, $message)
{
    if (! $condition) {
        throw new RuntimeException($message);
    }
}

/** A fresh editor for the given extension list (the project's default when none is given). */
function tiptap_editor($extensions = null)
{
    if ($extensions === null) {
        return new \Tiptap\Editor();
    }

    return new \Tiptap\Editor(['extensions' => $extensions]);
}

/** Render a document to HTML through the public editor API. */
function tiptap_html($document, $extensions = null)
{
    return tiptap_editor($extensions)->setContent($document)->getHTML();
}

/** Render a document to plain text through the public editor API. */
function tiptap_text($document, $extensions = null, $configuration = [])
{
    return tiptap_editor($extensions)->setContent($document)->getText($configuration);
}

/** Wrap a piece of text in the default document/paragraph shape. */
function tiptap_paragraph($text)
{
    return [
        'type' => 'doc',
        'content' => [[
            'type' => 'paragraph',
            'content' => $text,
        ]],
    ];
}
