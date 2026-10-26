<?php

namespace Sulu\Task\Harness;

use Twig\Environment;
use Twig\Loader\ArrayLoader;

class TestTwig extends Environment
{
    public function __construct()
    {
        parent::__construct(new ArrayLoader([]));
    }

    public function render($name, array $context = []): string
    {
        return '<html><body>preview shell</body></html>';
    }
}
