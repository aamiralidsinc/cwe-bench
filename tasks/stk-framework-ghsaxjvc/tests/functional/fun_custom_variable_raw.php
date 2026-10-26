<?php
require __DIR__ . '/../support/lib.php';

use Flarum\Extend;

h_assets_reset();
h_boot([
    (new Extend\Frontend('forum'))->css('/workspace/.htests/fixtures/raw_variable.less'),
    (new Extend\Theme())->addCustomLessVariable('extension-asset-path', function () {
        return '"http://assets.example.test/img.png"';
    }),
]);

$rendered = h_send(h_request('GET', '/'));
h_check((int) $rendered->getStatusCode() === 200, 'the forum renders with a raw extension LESS variable');

h_check(strpos(h_css(), '--asset:"http://assets.example.test/img.png"') !== false,
    'a quoted extension value is inserted raw, as documented');

echo "ok\n";
