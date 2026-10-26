<?php
/**
 * Folder uploads that carry a multi-level relative path still create the nested folders.
 */
return array(
    'name' => 'a multi-level folder path still creates nested folders',
    'run' => function (ElFinderTestContext $ctx) {
        $top = 'fold-' . $ctx->uniq();
        $resp = $ctx->get(array(
            'cmd' => 'mkdir',
            'target' => $ctx->hash('/'),
            'dirs' => array($top . '/sub/deep'),
        ));
        assert_not_server_error($resp, 'creating a nested folder path failed');
        $json = json_decode($resp['body'], true);
        assert_true(is_array($json) && empty($json['error']), 'creating a nested folder path returned an error');
        assert_true(is_dir($ctx->root . '/' . $top . '/sub/deep'), 'the nested folders were not created');
    },
);
