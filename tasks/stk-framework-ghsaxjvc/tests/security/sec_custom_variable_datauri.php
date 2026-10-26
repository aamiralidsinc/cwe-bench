<?php
require __DIR__ . '/../support/lib.php';

use Flarum\Extend;
use Flarum\Settings\SettingsRepositoryInterface;

h_assets_reset();
h_boot([
    (new Extend\Theme())->addCustomLessVariable('extension-asset-path', function () {
        return resolve(SettingsRepositoryInterface::class)->get('custom-prefix.extension_asset');
    }),
]);

$token = h_token();
$file = h_canary($token);

$payload = ";.embedded-value{background:data-uri('" . $file . "');}";

$response = h_send(h_request('POST', '/api/settings', [
    'theme_primary_color' => '#4D698E',
    'custom-prefix.extension_asset' => $payload,
], 1));

h_assert_no_read($response, 'custom-prefix.extension_asset', $payload, base64_encode($token));

echo "ok\n";
