<?php
/**
 * Bootstrap for the hidden suites: the project's own test bootstrap (autoloader + fallback class
 * loader) plus the shared hidden-case base class.
 */

require dirname(dirname(__DIR__)) . '/tests/bootstrap.php';
require __DIR__ . '/harness.php';
