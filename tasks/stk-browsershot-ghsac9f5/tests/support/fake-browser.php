<?php
// Offline renderer double. It receives exactly what the library hands to the browser
// client (the JSON command) and emulates only the parts the tests observe: reading the
// document, resolving the references the document makes, and writing the output file.
// Every local path it opens is appended to the log named by BS_TEST_LOG.
$args = $argv;
$raw = $args[2] ?? '';
if (str_starts_with($raw, '-f ')) {
    $raw = file_get_contents(substr($raw, 3));
}
$cmd = json_decode($raw, true) ?: [];
$action = $cmd['action'] ?? '';
$options = $cmd['options'] ?? [];
$log = getenv('BS_TEST_LOG') ?: '';

$appendLog = function (string $line) use ($log): void {
    if ($log !== '') {
        file_put_contents($log, $line . "\n", FILE_APPEND);
    }
};

$lower = fn (string $s): string => strtolower($s);

$localPath = function (string $url) use ($appendLog): ?string {
    $u = ltrim($url);
    $l = strtolower($u);
    if (str_starts_with($l, 'view-source:')) {
        $u = substr($u, strlen('view-source:'));
        $l = strtolower($u);
    }
    if (str_starts_with($l, 'file:\\')) {
        $u = 'file:' . str_replace('\\', '/', substr($u, 5));
        $l = strtolower($u);
    }
    if (str_starts_with($l, 'file:')) {
        $rest = substr($u, 5);
        if (str_starts_with($rest, '//')) {
            $rest = substr($rest, 2);
        } elseif (str_starts_with($rest, '/')) {
            // file:/abs -> /abs
        }
        $path = rawurldecode($rest);
        $appendLog($path);
        return $path;
    }
    return null;
};

$readLocal = function (string $url) use ($localPath): string {
    $p = $localPath($url);
    if ($p === null || ! is_file($p)) {
        return '';
    }
    return (string) file_get_contents($p);
};

$resolve = function (string $base, string $ref) : string {
    if (preg_match('~^[a-z][a-z0-9+.\-]*:~i', $ref)) {
        return $ref;
    }
    if (str_starts_with($ref, '//')) {
        return preg_replace('~^(file:).*~i', '$1', $base) . $ref;
    }
    $base = preg_replace('~/[^/]*$~', '/', $base);
    return $base . $ref;
};

$normalize = function (string $url): string {
    if (! preg_match('~^file:~i', $url)) {
        return $url;
    }
    $path = preg_replace('~^file://~i', '', $url);
    $path = preg_replace('~^file:~i', '', $path);
    $parts = explode('/', $path);
    $out = [];
    foreach ($parts as $p) {
        if ($p === '.' || $p === '') {
            continue;
        }
        if ($p === '..') {
            array_pop($out);
            continue;
        }
        $out[] = $p;
    }
    return 'file:///' . implode('/', $out);
};

$url = (string) ($cmd['url'] ?? '');
$contentUrl = isset($options['contentUrl']) ? (string) $options['contentUrl'] : '';
$body = '';
$pageUrl = $url;

if ($contentUrl !== '') {
    $body = $readLocal($url);          // the library's own temporary document
    $pageUrl = $contentUrl;
} else {
    $body = $readLocal($url);
    if ($body === '' && ! preg_match('~^file:~i', ltrim($url))) {
        $body = "REMOTE-OK";
    }
}

$leaked = [];
if (preg_match_all('/(?:src|href|action)\s*=\s*["\']([^"\']+)["\']/i', $body, $m)) {
    foreach ($m[1] as $ref) {
        $target = $normalize($resolve($pageUrl, $ref));
        if (preg_match('~^file:~i', $target)) {
            $leaked[] = $readLocal($target);
        }
    }
}
$rendered = $body . "\n" . implode("\n", $leaked);

if (isset($options['path']) && $options['path'] !== '') {
    file_put_contents($options['path'], $rendered);
    $result = '';
} else {
    $result = base64_encode($rendered);
}

echo json_encode([
    'result' => $result,
    'requestsList' => [],
    'consoleMessages' => [],
    'failedRequests' => [],
    'redirectHistory' => [],
    'pageErrors' => [],
]);
