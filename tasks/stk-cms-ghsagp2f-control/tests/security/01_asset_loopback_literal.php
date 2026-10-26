<?php
/**
 * An asset import whose URL is a loopback literal must be refused before it is contacted.
 */
require __DIR__ . '/../support/helpers.php';

$before = h_hits('18081');
$result = h_gql_import('http://127.0.0.1:18081/secret.js', 'poc.txt');
usleep(150000);

h_check(h_gql_refused($result), 'the import was not refused: ' . json_encode($result));
h_check(h_hits('18081') === $before, 'the internal service was contacted');
echo "ok\n";
