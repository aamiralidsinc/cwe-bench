<?php
/**
 * A new name supplied by the client must not move an existing item outside the storage root.
 */
return array(
    'name' => 'a new name with path segments cannot move an item outside the storage root',
    'run' => function (ElFinderTestContext $ctx) {
        $orig = 'original-' . $ctx->uniq() . '.txt';
        file_put_contents($ctx->root . '/' . $orig, "content\n");
        $name = 'moved-' . $ctx->uniq() . '.txt';
        $outside = $ctx->base . '/' . $name;

        $resp = $ctx->get(array(
            'cmd' => 'rename',
            'target' => $ctx->hash($orig),
            'name' => 'sub/../../' . $name,
        ));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_true(!file_exists($outside), 'the request moved an item outside the storage root');
    },
);
