<?php

declare(strict_types=1);

namespace CweBench\EcTrace;

use phpseclib3\Math\BigInteger;
use phpseclib3\Math\BigInteger\Engines\PHP64;

/**
 * A big-number engine that records every operation the library asks the engine to
 * perform. It behaves exactly like the bundled pure-PHP engine; it only appends the
 * operation's name to a log when recording is enabled.
 *
 * Engines are pluggable through the library's own selection API, which resolves an
 * engine by class name inside its namespace. Registering this class under that
 * namespace keeps the harness on the documented path.
 */
class RecordingEngine extends PHP64
{
    /** @var list<string> */
    public static $events = [];

    /** @var bool */
    public static $recording = false;

    private function note(string $operation): void
    {
        if (!self::$recording) {
            return;
        }
        // Record only operations the library itself requested (the immediate caller is
        // the BigInteger facade), never the engine's own internal helper calls.
        $trace = debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 4);
        $caller = $trace[2] ?? [];
        if (($caller['class'] ?? '') === BigInteger::class) {
            self::$events[] = $operation;
        }
    }

    public function add(PHP64 $y)
    {
        $this->note('add');
        return parent::add($y);
    }

    public function subtract(PHP64 $y)
    {
        $this->note('subtract');
        return parent::subtract($y);
    }

    public function multiply(PHP64 $y)
    {
        $this->note('multiply');
        return parent::multiply($y);
    }

    public function divide(PHP64 $y)
    {
        $this->note('divide');
        return parent::divide($y);
    }

    public function modInverse(PHP64 $n)
    {
        $this->note('modInverse');
        return parent::modInverse($n);
    }

    public function compare(PHP64 $y)
    {
        $this->note('compare');
        return parent::compare($y);
    }

    public function equals(PHP64 $x)
    {
        $this->note('equals');
        return parent::equals($x);
    }

    public function isNegative()
    {
        $this->note('isNegative');
        return parent::isNegative();
    }

    public function isOdd()
    {
        $this->note('isOdd');
        return parent::isOdd();
    }

    public function testBit($x)
    {
        $this->note('testBit');
        return parent::testBit($x);
    }

    public function negate()
    {
        $this->note('negate');
        return parent::negate();
    }

    public function bitwise_and(PHP64 $x)
    {
        $this->note('bitwise_and');
        return parent::bitwise_and($x);
    }

    public function bitwise_leftShift($shift)
    {
        $this->note('bitwise_leftShift');
        return parent::bitwise_leftShift($shift);
    }

    public function bitwise_rightShift($shift)
    {
        $this->note('bitwise_rightShift');
        return parent::bitwise_rightShift($shift);
    }
}

\class_alias(RecordingEngine::class, 'phpseclib3\\Math\\BigInteger\\Engines\\RecordingEngine');

final class Trace
{
    public static function install(): void
    {
        BigInteger::setEngine('RecordingEngine');
    }

    public static function reset(): void
    {
        RecordingEngine::$events = [];
    }

    /**
     * Run $operation and return the ordered list of big-number operations it requested.
     *
     * @return list<string>
     */
    public static function ops(callable $operation): array
    {
        self::reset();
        RecordingEngine::$recording = true;
        try {
            $operation();
        } finally {
            RecordingEngine::$recording = false;
        }
        return RecordingEngine::$events;
    }

    /**
     * Describe the first difference between two operation sequences, or null when they
     * are identical. Only the kind and order of operations is compared: the values are
     * expected to differ, the work is not.
     *
     * @param list<string> $a
     * @param list<string> $b
     */
    public static function difference(array $a, array $b): ?string
    {
        $common = min(count($a), count($b));
        for ($i = 0; $i < $common; $i++) {
            if ($a[$i] !== $b[$i]) {
                return sprintf('operation %d is %s for one scalar and %s for the other', $i, $a[$i], $b[$i]);
            }
        }
        if (count($a) !== count($b)) {
            return sprintf('different operation counts: %d and %d', count($a), count($b));
        }
        return null;
    }
}
