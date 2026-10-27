<?php
/**
 * Refusal-tolerant assertions for PHPUnit security tests. Copy into tests/support/.
 *
 * A security test that drives a hardened entry point must accept every secure outcome the instruction allows:
 * the call is refused (a client error, or one of the product's own refusal exceptions), or it completes and leaves
 * nothing unsafe behind. A crash is not a refusal: a 5xx, or an exception outside the declared refusal types, fails
 * the test, so a fix that merely breaks the call is still caught (wrong-fix class crash_as_refusal).
 *
 *   $out = Refusal::refusedOr(fn () => $user->setReturnUrl($payload),
 *       fn ($ret) => $this->assertStringNotContainsString('evil.example', (string) $ret),
 *       [\yii\web\ForbiddenHttpException::class]);
 *   $this->assertSame('/admin', $user->getReturnUrl());   // side effects are checked after every outcome
 */

namespace Bench\Support;

use PHPUnit\Framework\AssertionFailedError;

final class Refusal
{
    private static function status($o): ?int
    {
        if (!is_object($o)) {
            return null;
        }
        foreach (['statusCode', 'status', 'code'] as $p) {
            if (property_exists($o, $p) && is_int($o->$p) && $o->$p >= 100 && $o->$p <= 599) {
                return $o->$p;
            }
        }
        foreach (['getStatusCode', 'getStatus'] as $m) {
            if (method_exists($o, $m)) {
                $v = $o->$m();
                if (is_int($v) && $v >= 100 && $v <= 599) {
                    return $v;
                }
            }
        }
        return null;
    }

    /** @return array{refused: bool, value: mixed, reason: string} */
    public static function attempt(callable $call, array $refusals = []): array
    {
        try {
            $value = $call();
        } catch (AssertionFailedError $e) {
            throw $e;
        } catch (\Throwable $e) {
            $s = self::status($e);
            if ($s !== null) {
                if ($s >= 400 && $s < 500) {
                    return ['refused' => true, 'value' => null, 'reason' => get_class($e) . " $s"];
                }
                throw new AssertionFailedError("server error $s: a crash is not a refusal");
            }
            foreach ($refusals as $class) {
                if ($e instanceof $class) {
                    return ['refused' => true, 'value' => null, 'reason' => get_class($e)];
                }
            }
            throw $e;
        }
        $s = self::status($value);
        if ($s !== null && $s >= 400 && $s < 500) {
            return ['refused' => true, 'value' => $value, 'reason' => "status $s"];
        }
        if ($s !== null && $s >= 500) {
            throw new AssertionFailedError("server error $s: a crash is not a refusal");
        }
        return ['refused' => false, 'value' => $value, 'reason' => ''];
    }

    /** Passes when the call is refused, or when it completes and $ok accepts the result. */
    public static function refusedOr(callable $call, ?callable $ok = null, array $refusals = []): array
    {
        $out = self::attempt($call, $refusals);
        if (!$out['refused'] && $ok !== null && $ok($out['value']) === false) {
            throw new AssertionFailedError('the call completed and its result is unsafe');
        }
        return $out;
    }

    /** Passes only when the call is refused. */
    public static function mustRefuse(callable $call, array $refusals = []): array
    {
        $out = self::attempt($call, $refusals);
        if (!$out['refused']) {
            throw new AssertionFailedError('expected a refusal (a client error or a refusal exception)');
        }
        return $out;
    }
}
