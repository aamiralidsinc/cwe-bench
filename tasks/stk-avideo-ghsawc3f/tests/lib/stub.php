<?php
/**
 * Loopback stand-in for the main platform site used by the hidden suites.
 *
 * It answers the calls the application under test makes: decrypting the opaque job payload,
 * validating the API secret, validating a streamer token, acknowledging restream notifications,
 * and serving a fetchable stream manifest. Every request is recorded so a suite can see what the
 * application actually sent.
 */

$stubLog = '/tmp/avi-stub-requests.jsonl';
$notifyLog = '/tmp/avi-notify.json';

$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
file_put_contents($stubLog, json_encode([
    'method' => $_SERVER['REQUEST_METHOD'] ?? 'GET',
    'uri' => $_SERVER['REQUEST_URI'] ?? '/',
    'params' => $_REQUEST,
]) . "\n", FILE_APPEND);

header('Content-Type: application/json');

switch ($uri) {
    case '/plugin/API/get.json.php':
        $api = $_REQUEST['APIName'] ?? '';
        if ($api === 'decryptString') {
            $blob = $_POST['string'] ?? '';
            $json = base64_decode((string)$blob, true);
            $payload = is_string($json) ? json_decode($json, true) : null;
            if (is_array($payload)) {
                $payload['time'] = time();
            }
            echo json_encode(['error' => false, 'message' => json_encode($payload)]);
            return;
        }
        echo json_encode(['error' => false, 'msg' => 'ok']);
        return;

    case '/plugin/API/notify.ffmpeg.json.php':
        file_put_contents($notifyLog, json_encode($_REQUEST));
        echo json_encode(['error' => false, 'msg' => 'notified']);
        return;

    case '/plugin/Live/verifyToken.json.php':
        echo json_encode(['error' => false, 'msg' => 'ok']);
        return;

    case '/plugin/Live/view/Live_restreams/getLiveKey.json.php':
        echo json_encode([
            'error' => false,
            'stream_key' => 'stream-key',
            'stream_url' => 'rtmp://127.0.0.1/live',
            'live_url' => 'http://127.0.0.1/live',
        ]);
        return;

    case '/plugin/Live/view/Live_restreams_logs/add.json.php':
        echo json_encode(['error' => false]);
        return;

    case '/stream.m3u8':
        header('Content-Type: application/vnd.apple.mpegurl');
        echo "#EXTM3U\n";
        return;

    case '/media-tool-version':
        echo "ffmpeg version 6.1-static\n";
        return;
}

http_response_code(404);
echo json_encode(['error' => true, 'msg' => 'not found']);
