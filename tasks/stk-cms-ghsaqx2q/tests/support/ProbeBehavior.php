<?php

namespace CraftBench;

/**
 * Marker behavior used by the hidden suites: if a configuration can attach a behavior,
 * Yii instantiates this class and the marker file records it.
 */
class ProbeBehavior extends \yii\base\Behavior
{
    public static ?string $marker = null;

    public function init(): void
    {
        if (self::$marker !== null) {
            @file_put_contents(self::$marker, "behavior\n", FILE_APPEND);
        }
    }
}
