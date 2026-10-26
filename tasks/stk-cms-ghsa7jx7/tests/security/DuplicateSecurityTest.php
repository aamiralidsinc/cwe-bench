<?php

use Htest\Harness;
use Htest\MarkerBehavior;
use Htest\ProbeElement;
use PHPUnit\Framework\TestCase;

/**
 * The element duplication API must not construct classes named in
 * caller-supplied attributes or behavior configuration.
 */
final class DuplicateSecurityTest extends TestCase
{
    protected function setUp(): void
    {
        Harness::reset();
    }

    private function duplicate(array $attributes): void
    {
        $element = new ProbeElement(['id' => 1, 'siteId' => 1]);
        try {
            Harness::app()->getElements()->duplicateElement($element, $attributes);
        } catch (\Throwable $e) {
            \Htest\Refusal::assertRefusal($e);
        }
    }

    public function testBehaviorClassStringCannotBeConstructed(): void
    {
        $this->duplicate(['behaviors' => ['marker' => MarkerBehavior::class]]);
        self::assertSame(0, MarkerBehavior::$instances, 'a behavior class string was constructed');
    }

    public function testBehaviorConfigArrayCannotBeConstructed(): void
    {
        $this->duplicate(['behaviors' => ['marker' => ['class' => MarkerBehavior::class]]]);
        self::assertSame(0, MarkerBehavior::$instances, 'a behavior config array was constructed');
    }

    public function testAttributeConfigurationCannotAttachBehavior(): void
    {
        $this->duplicate(['as marker' => ['class' => MarkerBehavior::class]]);
        self::assertSame(0, MarkerBehavior::$instances, 'an attribute configuration attached a named class');
    }

    public function testSiteAttributeConfigurationCannotAttachBehavior(): void
    {
        $this->duplicate([
            'siteAttributes' => [
                1 => ['as marker' => ['class' => MarkerBehavior::class]],
            ],
        ]);
        self::assertSame(0, MarkerBehavior::$instances, 'a site attribute configuration attached a named class');
    }
}
