<?php
/**
 * The configured control-panel origin (port 18080). Logs every request so the cases can
 * tell an allowed same-origin fetch from a refused one.
 */
$path = (string)parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
@file_put_contents('/workspace/.htests/hits/18080.log', $path . "\n", FILE_APPEND);

switch ($path) {
    case '/cpresources/app.js':
        header('Content-Type: application/javascript');
        echo 'console.log("APP-JS-MARKER");';
        return true;
    case '/cpresources/same-redirect.js':
        header('Location: http://cp.test:18080/cpresources/app.js', true, 302);
        return true;
    case '/cpresources/redirect.js':
        header('Location: http://other.test:18081/secret.js', true, 302);
        return true;
}

http_response_code(404);
echo 'not found';
return true;
