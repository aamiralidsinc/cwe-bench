<?php
require __DIR__ . '/../support/lib.php';

h_assets_reset();
h_boot();

$token = h_token();
$file = h_canary($token);

$payload = "#4D698E;@import (inline) '" . $file . "';";

$response = h_send(h_request('POST', '/api/settings', [
    'theme_secondary_color' => $payload,
], 1));

h_assert_no_read($response, 'theme_secondary_color', $payload, $token);

echo "ok\n";
