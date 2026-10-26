<?php
/**
 * A temporary-file value that climbs several levels must not reach a file in the system
 * temporary directory.
 */
return array(
    'name' => 'archive download cannot return content far outside the temporary area',
    'run' => function (ElFinderTestContext $ctx) {
        $marker = 'DEEPER-' . $ctx->uniq();
        $name = 'deeper-' . $ctx->uniq() . '.txt';
        $victim = rtrim(sys_get_temp_dir(), DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . $name;
        file_put_contents($victim, $marker);

        $resp = $ctx->get(array(
            'cmd' => 'zipdl',
            'download' => '1',
            'targets' => array($ctx->hash('/'), '../../' . $name, 'report.txt', 'text/plain'),
        ));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_not_contains($marker, $resp['body'], 'the response returned the content of a file outside the temporary area');
        assert_true(is_file($victim), 'the request removed a file outside the temporary area');
        if (is_file($victim)) {
            unlink($victim);
        }
    },
);
