<?php
require __DIR__ . '/../support/lib.php';

h_assets_reset();
h_boot();

$token = h_token();
$file = h_canary($token);

$payload = '.embedded-value { background: data-uri(' . "'" . $file . "'" . '); }';

$response = h_send(h_request('POST', '/api/settings', [
    'custom_less' => $payload,
], 1));

h_assert_no_read($response, 'custom_less', $payload, base64_encode($token));

echo "ok\n";
