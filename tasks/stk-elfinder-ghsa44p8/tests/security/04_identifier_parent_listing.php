<?php
/**
 * A client-derived identifier must not expose the listing of a folder above the storage root.
 */
return array(
    'name' => 'a client-derived identifier cannot list a folder above the storage root',
    'run' => function (ElFinderTestContext $ctx) {
        $marker = 'PARENT-ENTRY-' . $ctx->uniq() . '.txt';
        file_put_contents($ctx->base . '/' . $marker, 'outside the storage root');

        $resp = $ctx->get(array('cmd' => 'ls', 'target' => $ctx->hash('..')));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_not_contains($marker, $resp['body'], 'the response listed an entry from above the storage root');
    },
);
