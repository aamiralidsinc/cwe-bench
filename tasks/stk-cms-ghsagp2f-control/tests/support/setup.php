<?php
/**
 * One-time verifier setup: installs Craft into the local MariaDB instance, creates the
 * volume and GraphQL schema the asset cases use, and writes state.json for the cases.
 */

require __DIR__ . '/bootstrap.php';

$app = \craft\test\TestSetup::warmCraft();
\Craft::$app = $app;
\Yii::$app = $app;

$db = $app->getDb();
$db->open();

if ($db->schema->getTableNames() !== []) {
    \craft\test\TestSetup::cleanseDb($db);
}

$site = new \craft\models\Site([
    'name' => 'Harness site',
    'handle' => 'default',
    'hasUrls' => true,
    'baseUrl' => 'http://cp.test:18080/',
    'language' => 'en-US',
    'primary' => true,
]);

$install = new \craft\migrations\Install([
    'db' => $db,
    'username' => 'harness',
    'password' => 'harness2018!!',
    'email' => 'harness@example.test',
    'site' => $site,
]);
$install->up(true);

$app->setIsInstalled();
$app->getSites()->refreshSites();
$app->getProjectConfig()->reset();

$volumePath = '/tmp/craft-harness-volume';
@mkdir($volumePath, 0777, true);

$fs = new \craft\fs\Local([
    'name' => 'Harness volume FS',
    'handle' => 'harnessFs',
    'path' => $volumePath,
]);
if (!$app->getFs()->saveFilesystem($fs)) {
    fwrite(STDERR, "FAIL: could not save filesystem: " . json_encode($fs->getErrors()) . "\n");
    exit(1);
}

$volume = new \craft\models\Volume([
    'name' => 'Site assets',
    'handle' => 'siteVolume',
    'fsHandle' => 'harnessFs',
]);
if (!$app->getVolumes()->saveVolume($volume)) {
    fwrite(STDERR, "FAIL: could not save volume: " . json_encode($volume->getErrors()) . "\n");
    exit(1);
}

$app->getProjectConfig()->saveModifiedConfigData();
$app->getProjectConfig()->reset();

$schema = new \craft\models\GqlSchema([
    'name' => 'Harness schema',
    'scope' => [
        "volumes.{$volume->uid}:edit",
        "volumes.{$volume->uid}:create",
    ],
]);
if (!$app->getGql()->saveSchema($schema)) {
    fwrite(STDERR, "FAIL: could not save GraphQL schema: " . json_encode($schema->getErrors()) . "\n");
    exit(1);
}
$app->getProjectConfig()->saveModifiedConfigData();

if ($schema->id === null) {
    $schema = $app->getGql()->getSchemaByUid($schema->uid);
}
if ($schema === null || $schema->id === null) {
    fwrite(STDERR, "FAIL: GraphQL schema was not persisted\n");
    exit(1);
}

@mkdir('/workspace/.htests/hits', 0777, true);

file_put_contents('/workspace/.htests/state.json', json_encode([
    'volumeUid' => $volume->uid,
    'volumeHandle' => $volume->handle,
    'schemaUid' => $schema->uid,
    'schemaId' => $schema->id,
]));

echo "setup ok\n";
