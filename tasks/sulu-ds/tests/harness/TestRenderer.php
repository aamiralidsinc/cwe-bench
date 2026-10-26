<?php

namespace Sulu\Task\Harness;

use Sulu\Bundle\PreviewBundle\Preview\Renderer\PreviewRendererInterface;

class TestRenderer implements PreviewRendererInterface
{
    public function render($object, $id, $partial = false, $options = [])
    {
        return '<html><body>rendered:' . $id . '</body></html>';
    }
}
