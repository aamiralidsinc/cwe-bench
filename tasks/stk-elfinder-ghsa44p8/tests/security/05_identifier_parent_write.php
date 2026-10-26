<?php
/**
 * The folder named by a client-derived identifier must stay inside the storage root when it is
 * used as the destination of a new item.
 */
return array(
    'name' => 'a client-derived identifier cannot create an item above the storage root',
    'run' => function (ElFinderTestContext $ctx) {
        $name = 'escaped-' . $ctx->uniq();
        $outside = $ctx->base . '/' . $name;

        $resp = $ctx->get(array('cmd' => 'mkdir', 'target' => $ctx->hash('..'), 'name' => $name));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_true(!file_exists($outside), 'the request created a folder above the storage root');
    },
);
