<?php
/**
 * An internal service the caller must never reach (port 18081). Every request is counted.
 */
$path = (string)parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
@file_put_contents('/workspace/.htests/hits/18081.log', $path . "\n", FILE_APPEND);
header('Content-Type: application/javascript');
echo 'TOP-SECRET-CANARY-MARKER';
return true;
