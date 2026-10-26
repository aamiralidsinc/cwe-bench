<?php

declare(strict_types=1);

// Hidden-suite bootstrap: the project's own autoloader, then the recording engine the
// work tests use (installed through the library's documented engine-selection API).
require __DIR__ . '/../vendor/autoload.php';
require __DIR__ . '/support/Trace.php';
require __DIR__ . '/support/Support.php';

\CweBench\EcTrace\Trace::install();
