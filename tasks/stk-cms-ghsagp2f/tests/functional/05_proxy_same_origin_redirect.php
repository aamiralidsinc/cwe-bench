<?php
/**
 * A redirect that stays on the resource origin keeps working.
 */
require __DIR__ . '/../support/helpers.php';

$before = h_hits('18080');
$result = h_proxy_dispatch('cp.test:18080', 'http://cp.test:18080/cpresources/same-redirect.js');
usleep(150000);

h_check($result['status'] === 200, 'the same-origin redirect failed: ' . json_encode($result));
h_check(str_contains($result['body'], 'APP-JS-MARKER'), 'the redirected body was not returned: ' . $result['body']);
echo "ok\n";
