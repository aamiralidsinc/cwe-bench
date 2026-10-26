<?php

namespace CraftTask\Harness;

/**
 * The property the hidden suites assert: a value the product stores or hands to the browser as a
 * navigation destination must not be able to execute script, and must not carry markup that would
 * be written into stored state. The check is deliberately written against the outcome, not against
 * any particular implementation, so a fix placed at any layer can satisfy it.
 */
final class Destination
{
    public const WEB_SCHEMES = ['http', 'https'];

    /**
     * Returns the scheme a browser would see, if the value names one.
     */
    public static function scheme(string $value): ?string
    {
        $value = ltrim($value);
        $scheme = parse_url($value, PHP_URL_SCHEME);
        if (is_string($scheme) && $scheme !== '') {
            return strtolower($scheme);
        }
        if (preg_match('/^\s*([a-z][a-z0-9+.\-]*)\s*:/i', $value, $match)) {
            return strtolower($match[1]);
        }
        return null;
    }

    /**
     * @return string[] Human-readable reasons the value is not a safe destination; empty when safe.
     */
    public static function problems(string $value): array
    {
        $problems = [];
        if (str_contains($value, '<') || str_contains($value, '>')) {
            $problems[] = 'markup';
        }
        $scheme = self::scheme($value);
        if ($scheme !== null && !in_array($scheme, self::WEB_SCHEMES, true)) {
            $problems[] = 'scheme:' . $scheme;
        }
        return $problems;
    }

    public static function isSafe(string $value): bool
    {
        return self::problems($value) === [];
    }
}
