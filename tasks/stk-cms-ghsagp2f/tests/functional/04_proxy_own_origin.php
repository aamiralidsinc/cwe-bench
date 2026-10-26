<?php
/**
 * The resource action keeps fetching a resource from the control panel's own origin.
 */
require __DIR__ . '/../support/helpers.php';

$before = h_hits('18080');
$result = h_proxy_dispatch('cp.test:18080', 'http://cp.test:18080/cpresources/app.js');
usleep(150000);

h_check($result['status'] === 200, 'the own-origin fetch failed: ' . json_encode($result));
h_check(str_contains($result['body'], 'APP-JS-MARKER'), 'the wrong body was returned: ' . $result['body']);
h_check(h_hits('18080') > $before, 'the resource origin was not contacted');
echo "ok\n";
