<?php
/**
 * General configuration for the hidden verification harness. The database and security key
 * are local fixtures; nothing here is reachable from the task image.
 */
return [
    'devMode' => true,
    'omitScriptNameInUrls' => true,
    'cpTrigger' => 'adminustriggerus',
    'slugWordSeparator' => '--',
    'allowUppercaseInSlug' => true,
    'securityKey' => 'cms-ghsagp2f-local-test-key',
];
