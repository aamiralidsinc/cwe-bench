<?php
/**
 * A folder name supplied by the client must not place the new folder outside the storage root.
 */
return array(
    'name' => 'a folder name with path segments cannot create a folder outside the storage root',
    'run' => function (ElFinderTestContext $ctx) {
        $name = 'escaped-' . $ctx->uniq();
        $outside = $ctx->base . '/' . $name;

        $resp = $ctx->get(array(
            'cmd' => 'mkdir',
            'target' => $ctx->hash('/'),
            'name' => 'sub/../../' . $name,
        ));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_true(!file_exists($outside), 'the request created a folder outside the storage root');
    },
);
