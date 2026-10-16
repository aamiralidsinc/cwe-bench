<?php

namespace CweTests;

use Filament\Tests\TestCase as FilamentTestCase;

abstract class TestCase extends FilamentTestCase
{
    protected function getPackageProviders($app): array
    {
        return array_merge(parent::getPackageProviders($app), [
            InaccessibleMfaPanelProvider::class,
        ]);
    }
}
