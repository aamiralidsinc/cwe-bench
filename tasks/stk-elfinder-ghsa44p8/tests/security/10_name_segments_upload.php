<?php
/**
 * An upload whose client-supplied name contains path segments must not be stored outside the
 * storage root.
 */
return array(
    'name' => 'an uploaded file with path segments cannot be stored outside the storage root',
    'run' => function (ElFinderTestContext $ctx) {
        $name = 'upload-' . $ctx->uniq() . '.png';
        $outside = $ctx->base . '/' . $name;

        $resp = $ctx->postMultipart(
            array(
                'cmd' => 'upload',
                'target' => $ctx->hash('/'),
                'name[]' => 'sub/../../' . $name,
            ),
            'upload[]',
            array(
                'filename' => 'image.png',
                'type' => 'image/png',
                'content' => "\x89PNG\r\n\x1a\n" . 'fixture',
            )
        );

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_true(!file_exists($outside), 'the request stored an uploaded file outside the storage root');
    },
);
