<?php
/**
 * Bootstrap for the hidden security / functional suites.
 *
 * The suites live under /workspace/.htests at grading time; this file only makes the shared
 * harness class available before PHPUnit loads the test classes.
 */
require_once dirname(__DIR__).'/harness/ApiTestCase.php';
