<?php
/**
 * Importing an asset from inline file data keeps working (no outbound request involved).
 */
require __DIR__ . '/../support/helpers.php';

$filename = 'inline-' . bin2hex(random_bytes(4)) . '.txt';
$result = h_gql_import_data('INLINE-FILE-MARKER', $filename);
$id = h_gql_asset_id($result);

h_check($id !== null, 'inline file data should still create an asset: ' . json_encode($result));
h_check(h_asset_content($id) === 'INLINE-FILE-MARKER', 'the inline content was not stored');
echo "ok\n";
