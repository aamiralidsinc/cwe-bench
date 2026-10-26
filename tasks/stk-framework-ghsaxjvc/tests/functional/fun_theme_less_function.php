<?php
require __DIR__ . '/../support/lib.php';

h_assets_reset();
h_boot();

$response = h_send(h_request('POST', '/api/settings', [
    'theme_secondary_color' => 'darken(#00ff00, 10%)',
], 1));

h_check((int) $response->getStatusCode() === 204, 'a colour expressed with a LESS function is accepted');

$rendered = h_send(h_request('GET', '/'));
h_check((int) $rendered->getStatusCode() === 200, 'the forum renders after saving the colour function');

h_check(strpos(h_css(), '--secondary-color:#0c0') !== false, 'the computed colour reaches the stylesheet');

echo "ok\n";
