<?php
/**
 * A link stored inside the browsed folder keeps working, including when its target lies outside
 * the browsed folder.
 */
return array(
    'name' => 'stored links to other locations are still listed, opened and read',
    'run' => function (ElFinderTestContext $ctx) {
        $marker = 'LINK-TARGET-' . $ctx->uniq();
        $target = $ctx->outside . '/link-target-' . $ctx->uniq();
        $ctx->mkdir($target);
        file_put_contents($target . '/inside.txt', $marker);

        $link = 'link-' . $ctx->uniq();
        assert_true(symlink($target, $ctx->root . '/' . $link), 'could not create the fixture link');

        $open = $ctx->get(array('cmd' => 'open', 'target' => $ctx->hash($link)));
        assert_not_server_error($open, 'opening the link failed');
        $json = json_decode($open['body'], true);
        assert_true(is_array($json) && empty($json['error']), 'opening the link returned an error');

        $ls = $ctx->get(array('cmd' => 'ls', 'target' => $ctx->hash($link)));
        assert_contains('inside.txt', $ls['body'], 'listing the link did not show its content');

        $read = $ctx->get(array('cmd' => 'file', 'target' => $ctx->hash($link . '/inside.txt')));
        assert_not_server_error($read, 'reading through the link failed');
        assert_contains($marker, $read['body'], 'reading a file through the link returned no content');
    },
);
