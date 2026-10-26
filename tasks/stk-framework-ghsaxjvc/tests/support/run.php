<?php
/**
 * Hidden-suite runner. Runs every case in its own process (so a case that hangs or corrupts
 * global state cannot affect the others) and writes a JUnit XML report.
 *
 * Usage: php run.php <security|functional> <junit-xml-path>
 */

$group = $argv[1] ?? '';
$out = $argv[2] ?? '';

if (! in_array($group, ['security', 'functional'], true) || $out === '') {
    fwrite(STDERR, "usage: php run.php <security|functional> <junit-xml-path>\n");
    exit(2);
}

$dir = "/workspace/.htests/{$group}";
$files = glob("{$dir}/*.php") ?: [];
sort($files);

if (! $files) {
    fwrite(STDERR, "no cases in {$group}\n");
    exit(2);
}

$results = [];

foreach ($files as $file) {
    $name = basename($file, '.php');
    $cmd = 'timeout -k 5 240 ' . escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg($file) . ' 2>&1';

    $output = [];
    $rc = 0;
    exec($cmd, $output, $rc);
    $message = trim(implode("\n", array_slice($output, -25)));

    $results[] = [
        'name' => $name,
        'ok' => $rc === 0,
        'message' => $message === '' ? "exit {$rc}" : $message,
    ];
}

$failures = count(array_filter($results, static fn (array $r): bool => ! $r['ok']));

$xml = '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
$xml .= sprintf(
    '<testsuite name="%s" tests="%d" failures="%d" errors="0">' . "\n",
    htmlspecialchars($group, ENT_QUOTES, 'UTF-8'),
    count($results),
    $failures
);

foreach ($results as $result) {
    $xml .= sprintf(
        '  <testcase classname="%s" name="%s">',
        htmlspecialchars($group, ENT_QUOTES, 'UTF-8'),
        htmlspecialchars($result['name'], ENT_QUOTES, 'UTF-8')
    );
    if ($result['ok']) {
        $xml .= "</testcase>\n";
    } else {
        $xml .= sprintf(
            '<failure message="%s">%s</failure></testcase>' . "\n",
            htmlspecialchars(substr($result['message'], 0, 500), ENT_QUOTES, 'UTF-8'),
            htmlspecialchars($result['message'], ENT_QUOTES, 'UTF-8')
        );
    }
}
$xml .= "</testsuite>\n";

if (@file_put_contents($out, $xml) === false) {
    fwrite(STDERR, "cannot write {$out}\n");
    exit(2);
}

printf("%s: %d/%d passed\n", $group, count($results) - $failures, count($results));
exit(0);
