<?php
/**
 * A file name supplied by the client must not place the new file outside the storage root.
 */
return array(
    'name' => 'a file name with path segments cannot create a file outside the storage root',
    'run' => function (ElFinderTestContext $ctx) {
        $name = 'escaped-' . $ctx->uniq() . '.txt';
        $outside = $ctx->base . '/' . $name;

        $resp = $ctx->get(array(
            'cmd' => 'mkfile',
            'target' => $ctx->hash('/'),
            'name' => 'sub/../../' . $name,
        ));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_true(!file_exists($outside), 'the request created a file outside the storage root');
    },
);
