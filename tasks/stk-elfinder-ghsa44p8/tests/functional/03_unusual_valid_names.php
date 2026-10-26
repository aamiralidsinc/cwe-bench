<?php
/**
 * Names that only look unusual still work: several dots, or a backslash (an ordinary character
 * in a name on this platform).
 */
return array(
    'name' => 'valid names containing dots or a backslash are still accepted',
    'run' => function (ElFinderTestContext $ctx) {
        $dotted = 'report..2024-' . $ctx->uniq() . '.txt';
        $resp = $ctx->get(array('cmd' => 'mkfile', 'target' => $ctx->hash('/'), 'name' => $dotted));
        assert_not_server_error($resp, 'creating a name with several dots failed');
        assert_true(is_file($ctx->root . '/' . $dotted), 'a name containing ".." was refused');

        $backslash = 'back\\slash-' . $ctx->uniq() . '.txt';
        $resp = $ctx->get(array('cmd' => 'mkfile', 'target' => $ctx->hash('/'), 'name' => $backslash));
        assert_not_server_error($resp, 'creating a name with a backslash failed');
        assert_true(is_file($ctx->root . '/' . $backslash), 'a name containing a backslash was refused');
    },
);
