<?php
/**
 * An asset import whose URL is a name that resolves to a loopback address must be refused.
 */
require __DIR__ . '/../support/helpers.php';

$before = h_hits('18081');
$result = h_gql_import('http://asset.test:18081/secret.js', 'poc.txt');
usleep(150000);

h_check(h_gql_refused($result), 'the import was not refused: ' . json_encode($result));
h_check(h_hits('18081') === $before, 'the internal service was contacted');
echo "ok\n";
