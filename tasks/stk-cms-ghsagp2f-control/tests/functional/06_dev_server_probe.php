<?php
/**
 * The operator-configured local dev-server probe keeps working.
 */
require __DIR__ . '/../support/helpers.php';

class TestAssetBundle extends \yii\web\AssetBundle
{
}

$before = h_hits('18082');
$app = craft_boot();
$server = $app->getWebpack()->getDevServer(TestAssetBundle::class);
usleep(150000);

h_check($server === 'https://cdn.example.test/', 'the dev server probe did not resolve: ' . var_export($server, true));
h_check(h_hits('18082') > $before, 'the configured dev server was not contacted');
echo "ok\n";
