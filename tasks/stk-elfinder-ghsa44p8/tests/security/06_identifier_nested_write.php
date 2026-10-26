<?php
/**
 * A nested spelling of the same identifier (a parent segment reached after a normal segment)
 * must not create anything above the storage root either.
 */
return array(
    'name' => 'a nested client-derived identifier cannot create an item above the storage root',
    'run' => function (ElFinderTestContext $ctx) {
        $name = 'escaped-' . $ctx->uniq();
        $outside = $ctx->base . '/' . $name;

        $resp = $ctx->get(array('cmd' => 'mkdir', 'target' => $ctx->hash('sub/../..'), 'name' => $name));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_true(!file_exists($outside), 'the request created a folder above the storage root');
    },
);
