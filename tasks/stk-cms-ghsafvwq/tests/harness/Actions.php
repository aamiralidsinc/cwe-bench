<?php

namespace CraftTask\Harness;

use Craft;
use craft\controllers\pluginstore\InstallController;
use craft\controllers\PreviewController;
use craft\controllers\UpdaterController;
use craft\web\Application;
use Throwable;
use yii\web\HttpException;

/**
 * Drives the product's real controller actions with a real request/response cycle. The setup
 * stubs only the services a database would normally supply (plugin installation and preview
 * tokens), so the controller, its base class and the response construction are the real ones.
 */
final class Actions
{
    /**
     * @return array{status:int, state:?array, exception:?string, message:?string}
     */
    public static function updaterIndex(Application $app, array $install, ?string $returnUrl): array
    {
        $_POST['install'] = $install;
        $_POST['packageNames'] = json_encode(['craft' => 'craftcms/cms']);
        if ($returnUrl === null) {
            unset($_POST['return']);
        } else {
            $_POST['return'] = $returnUrl;
        }
        $_REQUEST = array_merge($_GET, $_POST);

        return self::invoke($app, UpdaterController::class, 'updater', 'index', 'actionIndex',
            static function (Application $app): array {
                $js = '';
                foreach ($app->getView()->js as $block) {
                    $js .= implode("\n", $block);
                }
                $state = null;
                if (preg_match('/setState\((.*?)\);/s', $js, $match)) {
                    $decoded = json_decode($match[1], true);
                    if (is_array($decoded)) {
                        $state = $decoded;
                    }
                }
                return ['state' => $state];
            });
    }

    /**
     * @return array{status:int, state:?array, exception:?string, message:?string}
     */
    public static function installPlugin(Application $app, array $data, ?string $header, ?string $headerValue): array
    {
        $app->set('plugins', new PluginInstallStub($header, $headerValue));
        $_POST['data'] = $app->getSecurity()->hashData(json_encode($data));
        $_POST['packageNames'] = json_encode([$data['handle'] => $data['packageName']]);
        $_REQUEST = array_merge($_GET, $_POST);

        return self::invoke($app, InstallController::class, 'install', 'craft-install', 'actionCraftInstall',
            static function (Application $app): array {
                $response = $app->getResponse();
                $data = $response->data;
                return ['state' => is_array($data) ? $data : null];
            });
    }

    /**
     * @return array{status:int, location:?string, data:mixed, exception:?string, message:?string}
     */
    public static function previewCreateToken(Application $app, array $params): array
    {
        $app->getSession()->authorize('previewElement:' . ($params['canonicalId'] ?? '1'));
        $app->set('tokens', new PreviewTokenStub());
        $_POST = $params;
        $_REQUEST = array_merge($_GET, $_POST);

        return self::invoke($app, PreviewController::class, 'preview', 'create-token', 'actionCreateToken',
            static function (Application $app): array {
                $response = $app->getResponse();
                return [
                    'location' => $response->getHeaders()->get('Location'),
                    'data' => $response->data,
                ];
            });
    }

    /**
     * @param class-string $class
     * @return array{status:int, state:?array, location:?string, data:mixed, exception:?string, message:?string}
     */
    private static function invoke(Application $app, string $class, string $id, string $actionId,
                                   string $method, callable $inspect): array
    {
        try {
            /** @var \craft\web\Controller $controller */
            $controller = new $class($id, $app);
            $controller->enableCsrfValidation = false;
            $action = $controller->createAction($actionId);
            if (!$controller->beforeAction($action)) {
                return ['status' => 0, 'exception' => 'beforeAction', 'message' => 'beforeAction returned false'];
            }
            $response = $controller->$method();
            $result = ['status' => (int)$response->getStatusCode()];
            return array_merge($result, $inspect($app));
        } catch (HttpException $e) {
            return ['status' => (int)$e->statusCode, 'exception' => get_class($e), 'message' => $e->getMessage()];
        } catch (Throwable $e) {
            return ['status' => 500, 'exception' => get_class($e), 'message' => $e->getMessage()];
        }
    }

    public static function installData(string $handle = 'sample-plugin'): array
    {
        return [
            'packageName' => 'example/sample-plugin',
            'handle' => $handle,
            'edition' => 'standard',
            'returnUrl' => 'dashboard',
            'licenseKey' => null,
        ];
    }
}
