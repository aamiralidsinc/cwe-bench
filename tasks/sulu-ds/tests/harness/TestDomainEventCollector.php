<?php

namespace Sulu\Task\Harness;

use Sulu\Bundle\ActivityBundle\Application\Collector\DomainEventCollectorInterface;
use Sulu\Bundle\ActivityBundle\Domain\Event\DomainEvent;

class TestDomainEventCollector implements DomainEventCollectorInterface
{
    /**
     * @var DomainEvent[]
     */
    public array $events = [];

    public function collect(DomainEvent $domainEvent): void
    {
        $this->events[] = $domainEvent;
    }

    public function clear(): void
    {
        $this->events = [];
    }

    public function dispatch(): void
    {
    }
}
