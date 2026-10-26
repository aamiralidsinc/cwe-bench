<?php
/**
 * A multi-segment temporary-file value must not walk out of the temporary area either.
 */
return array(
    'name' => 'archive download cannot return content through a nested temporary-file value',
    'run' => function (ElFinderTestContext $ctx) {
        $marker = 'OUTSIDE-NESTED-' . $ctx->uniq();
        $name = 'victim-' . $ctx->uniq() . '.txt';
        $victim = $ctx->outside . '/' . $name;
        file_put_contents($victim, $marker);

        $resp = $ctx->get(array(
            'cmd' => 'zipdl',
            'download' => '1',
            'targets' => array($ctx->hash('/'), 'sub/../../outside/' . $name, 'report.txt', 'text/plain'),
        ));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_not_contains($marker, $resp['body'], 'the response returned the content of a file outside the temporary area');
        assert_true(is_file($victim), 'the request removed a file outside the temporary area');
    },
);
