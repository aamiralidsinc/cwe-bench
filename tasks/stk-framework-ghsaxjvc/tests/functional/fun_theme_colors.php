<?php
require __DIR__ . '/../support/lib.php';

h_assets_reset();
h_boot();

$response = h_send(h_request('POST', '/api/settings', [
    'theme_primary_color' => '#123456',
    'theme_secondary_color' => 'rgb(10, 20, 30)',
], 1));

h_check((int) $response->getStatusCode() === 204, 'ordinary theme colours are accepted');

$rendered = h_send(h_request('GET', '/'));
h_check((int) $rendered->getStatusCode() === 200, 'the forum renders after saving theme colours');

$css = h_css();
h_check(strpos($css, '--primary-color:#123456') !== false, 'the saved primary colour reaches the stylesheet');
h_check(strpos($css, '--secondary-color:#0a141e') !== false, 'the saved rgb colour reaches the stylesheet');

echo "ok\n";
