<?php
/**
 * A same-origin resource URL may redirect elsewhere. The redirect target must not be
 * contacted when it leaves the resource origin.
 */
require __DIR__ . '/../support/helpers.php';

$before = h_hits('18081');
$result = h_proxy_dispatch('cp.test:18080', 'http://cp.test:18080/cpresources/redirect.js');
usleep(150000);

h_check(h_proxy_refused($result), 'the proxy request was not refused: ' . json_encode($result));
h_check(h_hits('18081') === $before, 'the redirect target was contacted');
echo "ok\n";
