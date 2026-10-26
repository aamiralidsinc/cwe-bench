<?php
// @env CRAFT_TEST_GUZZLE_MOCK=1
/**
 * Importing an asset from an ordinary public URL keeps working.
 */
require __DIR__ . '/../support/helpers.php';

$filename = 'public-' . bin2hex(random_bytes(4)) . '.txt';
$result = h_gql_import(h_public_asset_url('pic.txt'), $filename);
$id = h_gql_asset_id($result);

h_check($id !== null, 'a public asset URL should still be imported: ' . json_encode($result));
h_check(h_asset_content($id) === 'MOCK-ASSET-MARKER-42', 'the fetched content was not stored');
echo "ok\n";
