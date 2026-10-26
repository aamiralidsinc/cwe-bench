<?php

namespace Htest;

use craft\controllers\FieldsController;
use craft\web\Application;
use craft\web\Request;
use yii\base\Behavior;
use yii\base\Component;

/**
 * A Yii behavior whose construction is the observable side effect of a config
 * being honoured. Tests assert that a hostile configuration never constructs it.
 */
class MarkerBehavior extends Behavior
{
    public static int $instances = 0;

    public function __construct($config = [])
    {
        self::$instances++;
        parent::__construct($config);
    }
}

/**
 * A behavior that records the component it was attached to, so a functional
 * test can prove that legitimate behavior attachment still happens.
 */
class RecordingBehavior extends Behavior
{
    /** @var array<int,array{owner:class-string,title:mixed}> */
    public static array $attached = [];

    public function attach($owner)
    {
        self::$attached[] = [
            'owner' => get_class($owner),
            'title' => $owner->title ?? null,
        ];
        parent::attach($owner);
    }
}

/**
 * A plain component configured with a behavior, standing in for the
 * application and plugin component configuration that must keep working.
 */
class TrustedComponent extends Component
{
    public string $label = '';
}

/**
 * A minimal element used to drive the duplication API without a database.
 */
class ProbeElement extends \craft\base\Element
{
    public function getFieldValues(?array $fieldHandles = null): array
    {
        return [];
    }

    public function getSupportedSites(): array
    {
        return [['siteId' => 1]];
    }
}

/**
 * Asserts the refusal form for a rejected configuration: a controlled client
 * error (or a successful request), never a fatal or a server error.
 */
final class Refusal
{
    public static function call(callable $call): void
    {
        try {
            $call();
        } catch (\Throwable $e) {
            self::assertRefusal($e);
        }
    }

    public static function assertRefusal(\Throwable $e): void
    {
            \PHPUnit\Framework\Assert::assertInstanceOf(
                \Exception::class,
                $e,
                'a refused configuration raised a fatal error instead of a client error',
            );
            \PHPUnit\Framework\Assert::assertNotInstanceOf(
                \yii\base\ErrorException::class,
                $e,
                'a refused configuration raised a PHP error instead of a client error',
            );
            \PHPUnit\Framework\Assert::assertNotInstanceOf(
                \yii\web\ServerErrorHttpException::class,
                $e,
            'a refused configuration produced a server error instead of a client error',
        );
    }
}

/**
 * Shared access to the Craft application built in the bootstrap.
 */
final class Harness
{
    public static function app(): Application
    {
        /** @var Application $app */
        $app = \Craft::$app;
        return $app;
    }

    public static function request(array $body): void
    {
        $request = self::app()->getRequest();
        if ($request instanceof Request) {
            $request->setBodyParams($body);
        }
    }

    public static function controller(): FieldsController
    {
        return new FieldsController('fields', self::app());
    }

    public static function reset(): void
    {
        MarkerBehavior::$instances = 0;
        RecordingBehavior::$attached = [];
        self::request([]);
    }
}
