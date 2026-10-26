<?php
/**
 * The resource URL can carry a userinfo component in front of the real host. The raw prefix
 * matches the resource base, but the contacted destination does not.
 */
require __DIR__ . '/../support/helpers.php';

$before = h_hits('18081');
$result = h_proxy_dispatch(
    'cp.test:18080',
    'http://cp.test:18080/cpresources@other.test:18081/secret.js'
);
usleep(150000);

h_check(h_proxy_refused($result), 'the proxy request was not refused: ' . json_encode($result));
h_check(h_hits('18081') === $before, 'the internal service was contacted');
echo "ok\n";
