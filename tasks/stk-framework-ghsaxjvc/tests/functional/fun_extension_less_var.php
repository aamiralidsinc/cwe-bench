<?php
require __DIR__ . '/../support/lib.php';

use Flarum\Extend;

h_assets_reset();
h_boot([
    (new Extend\Frontend('forum'))->css('/workspace/.htests/fixtures/extension_config.less'),
    (new Extend\Settings())->registerLessConfigVar('extension-config', 'custom-prefix.extension_config'),
], [
    'custom-prefix.extension_config' => 'customValue',
]);

$rendered = h_send(h_request('GET', '/'));
h_check((int) $rendered->getStatusCode() === 200, 'the forum renders with an extension-registered LESS variable');

h_check(strpos(h_css(), '--extension-config:customValue') !== false,
    'a free-form extension value still reaches the stylesheet');

echo "ok\n";
