<?php
require __DIR__ . '/../support/lib.php';

h_assets_reset();
h_boot();

$less = '.my-custom-block { color: #ff0000; .nested { border: 1px solid darken(#00ff00, 10%); } }';

$response = h_send(h_request('POST', '/api/settings', [
    'custom_less' => $less,
], 1));

h_check((int) $response->getStatusCode() === 204, 'ordinary custom LESS is accepted');

$rendered = h_send(h_request('GET', '/'));
h_check((int) $rendered->getStatusCode() === 200, 'the forum renders with the custom LESS');

$css = h_css();
h_check(strpos($css, '.my-custom-block{color:#ff0000}') !== false, 'the custom rule reaches the stylesheet');
h_check(strpos($css, '.my-custom-block .nested{border:1px solid #0c0}') !== false, 'nested rules and colour functions still compile');

echo "ok\n";
