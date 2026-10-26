<?php
require __DIR__ . '/../support/lib.php';

use Flarum\Extend;

h_assets_reset();
h_boot([
    (new Extend\Settings())->registerLessConfigVar('extension-color', 'custom-prefix.extension_color'),
]);

$token = h_token();
$file = h_canary($token);

$payload = "#4D698E;@import (inline) '" . $file . "';";

$response = h_send(h_request('POST', '/api/settings', [
    'custom-prefix.extension_color' => $payload,
], 1));

h_assert_no_read($response, 'custom-prefix.extension_color', $payload, $token);

echo "ok\n";
