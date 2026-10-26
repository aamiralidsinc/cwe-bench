<?php
/**
 * Sample deployment: serve the `files/` folder over the elFinder HTTP API.
 *
 * Run from the project root with PHP's built-in server:
 *     php -S 127.0.0.1:8080 -t .
 * and POST/GET commands to /connector.php (cmd=open, cmd=ls, ...).
 */

require __DIR__ . '/php/autoload.php';

$opts = array(
	'commonTempPath' => __DIR__ . DIRECTORY_SEPARATOR . '.tmp',
	'roots' => array(
		array(
			'driver'        => 'LocalFileSystem',
			'path'          => __DIR__ . DIRECTORY_SEPARATOR . 'files' . DIRECTORY_SEPARATOR,
			'URL'           => '/files/',
			'winHashFix'    => DIRECTORY_SEPARATOR !== '/',
			'uploadAllow'   => array('image', 'text/plain'),
			'uploadOrder'   => array('deny', 'allow'),
		),
	),
);

$connector = new elFinderConnector(new elFinder($opts));
$connector->run();
