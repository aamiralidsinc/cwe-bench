<?php
/**
 * Marker HTTP server used by the SSRF assertion. Every request that reaches it is recorded;
 * legitimate stylesheet compilation never contacts it.
 */

$hits = getenv('HARNESS_HITS') ?: '';

if ($hits !== '') {
    file_put_contents($hits, "hit " . ($_SERVER['REQUEST_URI'] ?? '') . "\n", FILE_APPEND);
}

header('Content-Type: text/css');
echo '.harness-marker{color:red}';
