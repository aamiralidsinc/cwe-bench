<?php
require __DIR__ . '/../support/lib.php';

list($process, $port, $hits) = h_listener_start();

h_assets_reset();
h_boot();

$payload = "#4D698E;@import (inline) url('http://127.0.0.1:" . $port . "/x.css');";

$response = h_send(h_request('POST', '/api/settings', [
    'theme_primary_color' => $payload,
], 1));

$status = (int) $response->getStatusCode();

if ($status >= 200 && $status < 300) {
    h_send(h_request('GET', '/'));
}

usleep(300000);

$count = h_listener_hits($hits);
h_listener_stop($process);

h_check($count === 0, 'the submitted value did not make the server contact a network endpoint');
h_check($status >= 200 && $status < 500, "the submit produced a usable answer (got {$status})");

echo "ok\n";
