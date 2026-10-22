<?php
declare(strict_types=1);

/*
 * Test bootstrap for the hidden verifier tests.
 *
 * The project itself is not runnable as a standalone app (its unit-test bootstrap
 * expects the pimcore skeleton project); the task exercises the model and class
 * builder directly against /workspace/vendor/autoload.php. Nothing here needs a network
 * or a database.
 */

define('PIMCORE_PROJECT_ROOT', '/workspace');

require '/workspace/vendor/autoload.php';

$pimcoreTaskVar = '/tmp/pimcore-task-var';
@mkdir($pimcoreTaskVar . '/classes', 0777, true);
@mkdir($pimcoreTaskVar . '/custom', 0777, true);

define('PIMCORE_CLASS_DIRECTORY', $pimcoreTaskVar . '/classes');
define('PIMCORE_CLASS_DEFINITION_DIRECTORY', $pimcoreTaskVar . '/classes');
define('PIMCORE_CUSTOM_CONFIGURATION_CLASS_DEFINITION_DIRECTORY', $pimcoreTaskVar . '/custom');

require_once __DIR__ . '/src/Harness.php';
