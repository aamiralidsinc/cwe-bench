<?php
/**
 * Shared helpers for the hidden security and functional cases.
 */

require_once __DIR__ . '/bootstrap.php';

function h_state(): array
{
    static $state = null;
    if ($state === null) {
        $raw = @file_get_contents('/workspace/.htests/state.json');
        $state = $raw ? json_decode($raw, true) : [];
    }
    return is_array($state) ? $state : [];
}

function h_hits(string $port): int
{
    $file = "/workspace/.htests/hits/$port.log";
    if (!is_file($file)) {
        return 0;
    }
    $lines = file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [];
    return count($lines);
}

function h_check(bool $ok, string $message): void
{
    if (!$ok) {
        fwrite(STDERR, "FAIL: $message\n");
        exit(1);
    }
}

/**
 * Runs the asset-save mutation through Craft's GraphQL service.
 */
function h_gql_import(string $url, string $filename): array
{
    $app = craft_boot();
    $state = h_state();
    $schema = $app->getGql()->getSchemaById((int)($state['schemaId'] ?? 0));
    if ($schema === null) {
        fwrite(STDERR, "FAIL: no GraphQL schema in the harness state\n");
        exit(1);
    }

    $query = sprintf(
        'mutation { save_%s_Asset(_file: {url: %s, filename: %s}) { id } }',
        $state['volumeHandle'],
        json_encode($url),
        json_encode($filename)
    );

    return $app->getGql()->executeQuery($schema, $query, [], null, true);
}

/**
 * Runs the asset-save mutation with inline base64 data instead of a URL.
 */
function h_gql_import_data(string $payload, string $filename): array
{
    $app = craft_boot();
    $state = h_state();
    $schema = $app->getGql()->getSchemaById((int)($state['schemaId'] ?? 0));
    if ($schema === null) {
        fwrite(STDERR, "FAIL: no GraphQL schema in the harness state\n");
        exit(1);
    }

    $query = sprintf(
        'mutation { save_%s_Asset(_file: {fileData: %s, filename: %s}) { id } }',
        $state['volumeHandle'],
        json_encode('data:text/plain;base64,' . base64_encode($payload)),
        json_encode($filename)
    );

    return $app->getGql()->executeQuery($schema, $query, [], null, true);
}

function h_gql_asset_id(array $result): ?int
{
    $state = h_state();
    $id = $result['data']['save_' . $state['volumeHandle'] . '_Asset']['id'] ?? null;
    return $id === null ? null : (int)$id;
}

/**
 * Whether the GraphQL response is a deliberate client-visible refusal rather than a crash.
 */
function h_gql_refused(array $result): bool
{
    if (!empty(h_gql_asset_id($result))) {
        return false;
    }
    if (empty($result['errors']) || !is_array($result['errors'])) {
        return false;
    }
    foreach ($result['errors'] as $error) {
        if (($error['message'] ?? '') !== 'Internal server error') {
            return true;
        }
    }
    return false;
}

function h_asset_content(int $id): ?string
{
    craft_boot();
    $asset = \craft\elements\Asset::find()->id($id)->one();
    if ($asset === null) {
        return null;
    }
    return (string)$asset->getContents();
}

/**
 * Dispatches the control-panel resource action with the given Host header.
 *
 * @return array{status:int, body:string, exception:?string}
 */
function h_proxy_dispatch(string $host, string $url): array
{
    $segments = explode(':', $host, 2);
    $hostName = $segments[0];
    $hostPort = $segments[1] ?? '80';

    $app = craft_boot([
        'HTTP_HOST' => $host,
        'SERVER_NAME' => $hostName,
        'SERVER_PORT' => $hostPort,
        'REQUEST_URI' => '/adminustriggerus/app/resource-js?url=' . rawurlencode($url),
        'SCRIPT_NAME' => '/index.php',
        'SCRIPT_FILENAME' => '/workspace/web/index.php',
        'REQUEST_METHOD' => 'GET',
        'HTTPS' => '',
    ]);

    try {
        $response = $app->runAction('app/resource-js', ['url' => $url]);
        return [
            'status' => (int)$response->getStatusCode(),
            'body' => (string)$response->data,
            'exception' => null,
        ];
    } catch (\Throwable $e) {
        $status = $e instanceof \yii\web\HttpException ? (int)$e->statusCode : 599;
        return [
            'status' => $status,
            'body' => '',
            'exception' => get_class($e) . ': ' . $e->getMessage(),
        ];
    }
}

function h_proxy_refused(array $result): bool
{
    return $result['status'] >= 400 && $result['status'] < 500;
}

function h_public_asset_url(string $path): string
{
    return 'http://assets.example.test/' . ltrim($path, '/');
}
