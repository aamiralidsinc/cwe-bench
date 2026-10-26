<?php
declare(strict_types=1);

// Usage: probe.php <autoload.php> <mode> <file>
// Prints REFUSED when the call reports a handled refusal, PROCEEDED when it succeeds.
// A fatal error (memory exhaustion) or a timeout leaves no marker and a non-zero exit.
use PhpOffice\PhpSpreadsheet\Reader\Gnumeric;
use PhpOffice\PhpSpreadsheet\Reader\Ods;
use PhpOffice\PhpSpreadsheet\Reader\Xls;
use PhpOffice\PhpSpreadsheet\Reader\Xlsx;
use PhpOffice\PhpSpreadsheet\Shared\OLE;

require $argv[1];

$mode = $argv[2];
$path = $argv[3];

try {
    switch ($mode) {
        case 'gnm_canread':
            if ((new Gnumeric())->canRead($path) === false) {
                echo "REFUSED\n";
                exit(0);
            }
            break;
        case 'gnm_load':
            (new Gnumeric())->load($path);
            break;
        case 'gnm_names':
            (new Gnumeric())->listWorksheetNames($path);
            break;
        case 'gnm_info':
            (new Gnumeric())->listWorksheetInfo($path);
            break;
        case 'xls_canread':
            if ((new Xls())->canRead($path) === false) {
                echo "REFUSED\n";
                exit(0);
            }
            break;
        case 'xls_load':
            (new Xls())->load($path);
            break;
        case 'xls_names':
            (new Xls())->listWorksheetNames($path);
            break;
        case 'xls_info':
            (new Xls())->listWorksheetInfo($path);
            break;
        case 'ole_read':
            (new OLE())->read($path);
            break;
        case 'xlsx_canread':
            if ((new Xlsx())->canRead($path) === false) {
                echo "REFUSED\n";
                exit(0);
            }
            break;
        case 'xlsx_load':
            (new Xlsx())->load($path);
            break;
        case 'ods_canread':
            if ((new Ods())->canRead($path) === false) {
                echo "REFUSED\n";
                exit(0);
            }
            break;
        case 'ods_load':
            (new Ods())->load($path);
            break;
        default:
            fwrite(STDERR, "unknown mode $mode\n");
            exit(2);
    }
    echo "PROCEEDED\n";
    exit(0);
} catch (Throwable $e) {
    echo 'REFUSED ' . get_class($e) . "\n";
    exit(0);
}
