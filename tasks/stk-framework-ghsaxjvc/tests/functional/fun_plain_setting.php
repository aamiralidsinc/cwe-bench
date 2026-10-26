<?php
require __DIR__ . '/../support/lib.php';

h_assets_reset();
h_boot();

$response = h_send(h_request('POST', '/api/settings', [
    'custom-prefix.plain_value' => 'hello world',
], 1));

h_check((int) $response->getStatusCode() === 204, 'an ordinary setting save is accepted');
h_check(h_setting('custom-prefix.plain_value') === 'hello world', 'the ordinary setting is stored');

echo "ok\n";
