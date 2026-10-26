<?php
/**
 * The temporary-file value must not be usable to read or remove a stored file of the volume
 * (a location that is outside the temporary area but inside the browsed storage root).
 */
return array(
    'name' => 'archive download cannot read or remove a stored file through its temporary-file value',
    'run' => function (ElFinderTestContext $ctx) {
        $marker = 'STORED-' . $ctx->uniq();
        $name = 'stored-' . $ctx->uniq() . '.txt';
        $victim = $ctx->root . '/' . $name;
        file_put_contents($victim, $marker);

        $resp = $ctx->get(array(
            'cmd' => 'zipdl',
            'download' => '1',
            'targets' => array($ctx->hash('/'), '../root/' . $name, 'report.txt', 'text/plain'),
        ));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_not_contains($marker, $resp['body'], 'the response returned the content of a stored file');
        assert_true(is_file($victim), 'the request removed a stored file');
    },
);
