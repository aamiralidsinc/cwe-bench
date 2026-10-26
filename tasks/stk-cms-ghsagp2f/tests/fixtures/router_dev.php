<?php
/**
 * An operator-configured local dev server (port 18082) used by the coupled functional case.
 */
$path = (string)parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
@file_put_contents('/workspace/.htests/hits/18082.log', $path . "\n", FILE_APPEND);

if ($path === '/which-asset') {
    header('Content-Type: application/json');
    echo json_encode(['classes' => ['TestAssetBundle']]);
    return true;
}

http_response_code(404);
echo 'not found';
return true;
