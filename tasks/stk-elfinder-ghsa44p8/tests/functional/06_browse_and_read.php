<?php
/**
 * Normal browsing and reading of the storage root keeps working.
 */
return array(
    'name' => 'browsing and reading the storage root still works',
    'run' => function (ElFinderTestContext $ctx) {
        $open = $ctx->get(array('cmd' => 'open', 'target' => $ctx->hash('/')));
        assert_not_server_error($open, 'opening the root failed');
        $json = json_decode($open['body'], true);
        assert_true(is_array($json) && empty($json['error']), 'opening the root returned an error');
        assert_true(isset($json['cwd']['mime']) && $json['cwd']['mime'] === 'directory', 'the root was not reported as a folder');

        $ls = $ctx->get(array('cmd' => 'ls', 'target' => $ctx->hash('/')));
        assert_contains('seed.txt', $ls['body'], 'listing the root did not show its content');

        $read = $ctx->get(array('cmd' => 'file', 'target' => $ctx->hash('seed.txt')));
        assert_not_server_error($read, 'reading a stored file failed');
        assert_contains('fixture seed', $read['body'], 'reading a stored file returned no content');
    },
);
