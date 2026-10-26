<?php
/**
 * The control-panel resource action with a request Host naming an internal service, and a
 * resource URL under that Host, must not fetch the internal service.
 */
require __DIR__ . '/../support/helpers.php';

$before = h_hits('18081');
$result = h_proxy_dispatch('127.0.0.1:18081', 'http://127.0.0.1:18081/cpresources/secret.js');
usleep(150000);

h_check(h_proxy_refused($result), 'the proxy request was not refused: ' . json_encode($result));
h_check(h_hits('18081') === $before, 'the internal service was contacted');
echo "ok\n";
