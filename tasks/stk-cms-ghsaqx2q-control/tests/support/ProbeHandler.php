<?php

namespace CraftBench;

/**
 * Marker handler used by the hidden suites: if a configuration can register an event
 * handler, Yii calls this static method and the marker file records it.
 */
class ProbeHandler
{
    public static function handle($event = null): void
    {
        if (ProbeBehavior::$marker !== null) {
            @file_put_contents(ProbeBehavior::$marker, "handler\n", FILE_APPEND);
        }
    }
}
