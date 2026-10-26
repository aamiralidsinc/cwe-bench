<?php

declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';

foreach (glob(__DIR__.'/support/*.php') as $file) {
    require_once $file;
}
