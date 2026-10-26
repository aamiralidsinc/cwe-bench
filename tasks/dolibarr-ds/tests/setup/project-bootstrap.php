<?php
/**
 * Bootstrap for the project's own PHPUnit tests. They are copied into the application's
 * test/phpunit directory at grading time so their relative includes resolve. Loading the
 * date helpers here is enough for the leave tests, which use them without requiring the
 * library themselves.
 */
require_once '/workspace/htdocs/master.inc.php';
require_once '/workspace/htdocs/core/lib/date.lib.php';
