<?php

namespace CraftTask\Harness;

use craft\elements\User;
use craft\test\TestSetup;
use craft\web\Application;
use PHPUnit\Framework\TestCase;

abstract class CraftTestCase extends TestCase
{
    protected const SECURITY_KEY = 'craftcms-task-local-key-0123456789abcdef';
    protected const HOST = 'test.craftcms.test';

    protected ?Application $app = null;

    protected function tearDown(): void
    {
        if ($this->app !== null) {
            TestSetup::tearDownCraft();
            $this->app = null;
        }
        parent::tearDown();
    }

    /**
     * Boots the application for one request. Globals must be in place before the application is
     * created because the request component reads them during initialization.
     */
    protected function boot(array $post = [], array $get = [], string $uri = '/adminustriggerus/'): Application
    {
        $_SERVER['REQUEST_METHOD'] = $post === [] ? 'GET' : 'POST';
        $_SERVER['REQUEST_URI'] = $uri;
        $_SERVER['SCRIPT_NAME'] = '/index.php';
        $_SERVER['SCRIPT_FILENAME'] = CRAFT_ROOT_PATH . '/web/index.php';
        $_SERVER['HTTP_HOST'] = self::HOST;
        $_SERVER['SERVER_NAME'] = self::HOST;
        $_SERVER['SERVER_PORT'] = '443';
        $_SERVER['HTTPS'] = 'on';
        $_SERVER['REMOTE_ADDR'] = '127.0.0.1';
        $_SERVER['REMOTE_PORT'] = '65432';
        $_GET = $get;
        $_POST = $post;
        $_REQUEST = array_merge($get, $post);
        $_FILES = [];
        $_COOKIE = [];

        $app = TestSetup::warmCraft();
        $app->getRequest()->cookieValidationKey = self::SECURITY_KEY;
        $general = $app->getConfig()->getGeneral();
        $general->securityKey = self::SECURITY_KEY;
        $general->allowUpdates = true;
        $general->allowAdminChanges = true;
        $general->enableCsrfProtection = false;

        $this->app = $app;
        return $app;
    }

    protected function asAdmin(): User
    {
        $user = new User(['id' => 1, 'admin' => true, 'username' => 'admin']);
        $this->app->getUser()->setIdentity($user);
        return $user;
    }

    protected static function assertSafeDestination(string $value, string $context): void
    {
        self::assertSame([], Destination::problems($value),
            $context . ' is not a safe navigation destination: ' . var_export($value, true));
    }

    protected static function assertExactDestination(string $expected, string $actual, string $context): void
    {
        self::assertSame($expected, $actual, $context . ' must keep working unchanged');
    }

    /**
     * A refusal must be a client error. 2xx/3xx responses are only acceptable when the
     * destination they carry (if any) is safe.
     */
    protected static function assertRefusedOrSafe(array $result, ?string $destination, string $context): void
    {
        $status = (int)($result['status'] ?? 0);
        self::assertLessThan(500, $status, $context . ': a server error is not a refusal');
        if ($status >= 400) {
            return;
        }
        if ($destination === null) {
            return; // the request produced no navigation destination at all
        }
        self::assertSafeDestination($destination, $context);
    }
}
