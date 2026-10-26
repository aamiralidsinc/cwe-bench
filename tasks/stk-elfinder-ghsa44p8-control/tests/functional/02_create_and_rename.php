<?php
/**
 * Ordinary creation and renaming still work.
 */
return array(
    'name' => 'creating and renaming items still works',
    'run' => function (ElFinderTestContext $ctx) {
        $dir = 'folder-' . $ctx->uniq();
        $mkdir = $ctx->get(array('cmd' => 'mkdir', 'target' => $ctx->hash('/'), 'name' => $dir));
        assert_not_server_error($mkdir, 'mkdir failed');
        $json = json_decode($mkdir['body'], true);
        assert_true(is_array($json) && empty($json['error']), 'mkdir returned an error');
        assert_true(is_dir($ctx->root . '/' . $dir), 'mkdir did not create the folder');

        $file = 'note-' . $ctx->uniq() . '.txt';
        $mkfile = $ctx->get(array('cmd' => 'mkfile', 'target' => $ctx->hash('/'), 'name' => $file));
        assert_not_server_error($mkfile, 'mkfile failed');
        $json = json_decode($mkfile['body'], true);
        assert_true(is_array($json) && empty($json['error']), 'mkfile returned an error');
        assert_true(is_file($ctx->root . '/' . $file), 'mkfile did not create the file');

        $renamed = 'renamed-' . $ctx->uniq() . '.txt';
        $rename = $ctx->get(array('cmd' => 'rename', 'target' => $ctx->hash($file), 'name' => $renamed));
        assert_not_server_error($rename, 'rename failed');
        $json = json_decode($rename['body'], true);
        assert_true(is_array($json) && empty($json['error']), 'rename returned an error');
        assert_true(is_file($ctx->root . '/' . $renamed), 'rename did not move the file');
    },
);
