<?php
/**
 * The archive download must not read a file outside the server's temporary area.
 */
return array(
    'name' => 'archive download cannot return content from outside the temporary area',
    'run' => function (ElFinderTestContext $ctx) {
        $marker = 'OUTSIDE-READ-' . $ctx->uniq();
        $name = 'victim-' . $ctx->uniq() . '.txt';
        $victim = $ctx->outside . '/' . $name;
        file_put_contents($victim, $marker);

        $resp = $ctx->get(array(
            'cmd' => 'zipdl',
            'download' => '1',
            'targets' => array($ctx->hash('/'), '../outside/' . $name, 'report.txt', 'text/plain'),
        ));

        assert_not_server_error($resp, 'the server failed instead of refusing the request');
        assert_not_contains($marker, $resp['body'], 'the response returned the content of a file outside the temporary area');
        assert_true(is_file($victim), 'the request removed a file outside the temporary area');
        assert_true(file_get_contents($victim) === $marker, 'the request changed a file outside the temporary area');
    },
);
