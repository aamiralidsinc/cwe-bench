<?php
/**
 * General configuration for the hidden verification harness. The security key and the paths are
 * local fixtures; nothing here is reachable from the task image.
 */
return [
    'devMode' => true,
    'omitScriptNameInUrls' => true,
    'cpTrigger' => 'adminustriggerus',
    'securityKey' => 'craftcms-task-local-key-0123456789abcdef',
    'allowUpdates' => true,
    'allowAdminChanges' => true,
    'enableCsrfProtection' => false,
    'resourceBasePath' => '/tmp/craft-task-resources',
];
