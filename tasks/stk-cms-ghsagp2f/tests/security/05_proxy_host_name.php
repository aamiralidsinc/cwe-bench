<?php
/**
 * The same request with a Host name that resolves to the internal service.
 */
require __DIR__ . '/../support/helpers.php';

$before = h_hits('18081');
$result = h_proxy_dispatch('asset.test:18081', 'http://asset.test:18081/cpresources/secret.js');
usleep(150000);

h_check(h_proxy_refused($result), 'the proxy request was not refused: ' . json_encode($result));
h_check(h_hits('18081') === $before, 'the internal service was contacted');
echo "ok\n";
