<?php
require __DIR__ . '/../support/lib.php';

h_assets_reset();
h_boot();

$payload = '@muralf';

$response = h_send(h_request('POST', '/api/settings', [
    'custom_less' => $payload,
], 1));

$status = (int) $response->getStatusCode();
h_check($status >= 400 && $status < 500, "invalid LESS is still refused with a client error (got {$status})");
h_check(h_setting('custom_less') !== $payload, 'invalid LESS is not stored');

echo "ok\n";
