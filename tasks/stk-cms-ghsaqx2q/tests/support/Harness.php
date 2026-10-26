<?php

declare(strict_types=1);

namespace CraftBench;

use Craft;
use craft\elements\conditions\ElementCondition;
use craft\elements\conditions\IdConditionRule;
use craft\elements\conditions\users\AdminConditionRule;
use craft\elements\conditions\users\UserCondition;
use craft\elements\Entry;
use craft\helpers\Json;
use craft\helpers\StringHelper;
use craft\models\Section;
use craft\models\Section_SiteSettings;
use craft\services\ProjectConfig;
use craft\web\Application;

/**
 * Fixture and entry-point helpers shared by the hidden suites.
 */
final class Harness
{
    public const SECTION_HANDLE = 'craftBenchNews';

    public static Section $section;

    public static Application $app;

    public static ?string $lastEntryTypeHandle = null;

    public static function init(Application $app): void
    {
        self::$app = $app;

        // Keep project config changes in the database; do not write YAML files.
        $app->getProjectConfig()->writeYamlAutomatically = false;

        $section = $app->getSections()->getSectionByHandle(self::SECTION_HANDLE);
        if ($section === null) {
            $site = $app->getSites()->getPrimarySite();
            $siteSettings = new Section_SiteSettings([
                'siteId' => $site->id,
                'enabledByDefault' => true,
                'hasUrls' => true,
                'uriFormat' => 'craftbench/{slug}',
                'template' => 'craftbench/_entry',
            ]);
            $section = new Section([
                'name' => 'CraftBench News',
                'handle' => self::SECTION_HANDLE,
                'type' => Section::TYPE_CHANNEL,
                'siteSettings' => [$site->id => $siteSettings],
            ]);
            if (!$app->getSections()->saveSection($section)) {
                throw new \RuntimeException('Unable to create the fixture section');
            }
            $section = $app->getSections()->getSectionByHandle(self::SECTION_HANDLE);
        }
        self::$section = $section;

        $admin = $app->getUsers()->getUserByUsernameOrEmail('craftcms');
        if ($admin === null) {
            throw new \RuntimeException('Unable to find the installed administrator');
        }
        $app->getUser()->setIdentity($admin);
    }

    /** Returns a fresh marker path and points the probes at it. */
    public static function newMarker(): string
    {
        $path = sys_get_temp_dir() . '/craftbench-' . bin2hex(random_bytes(8));
        @unlink($path);
        ProbeBehavior::$marker = $path;
        return $path;
    }

    public static function markerHit(string $path): bool
    {
        return is_file($path) && filesize($path) > 0;
    }

    public static function sourceKey(): string
    {
        return 'section:' . self::$section->uid;
    }

    /** An element config that carries a behavior or an event-handler entry. */
    public static function attackElement(string $vector = 'as'): array
    {
        $element = [
            'type' => \craft\fieldlayoutelements\Heading::class,
            'heading' => 'CraftBench',
        ];
        if ($vector === 'on') {
            $element['on init'] = ProbeHandler::class . '::handle';
        } elseif ($vector === 'as') {
            $element['as craftBenchProbe'] = ['class' => ProbeBehavior::class];
        }
        return $element;
    }

    /**
     * A layout config whose unwanted wiring sits at the layout, tab or element level.
     */
    public static function attackLayout(string $level = 'root', string $vector = 'as', bool $stringElements = false): array
    {
        $elements = [self::attackElement($level === 'element' ? $vector : 'none')];
        if ($stringElements) {
            $elements = Json::encode($elements);
        }

        $tab = [
            'name' => 'Content',
            'elements' => $elements,
        ];
        $layout = [
            'tabs' => [$tab],
        ];

        if ($level === 'tab') {
            if ($vector === 'on') {
                $layout['tabs'][0]['on init'] = ProbeHandler::class . '::handle';
            } else {
                $layout['tabs'][0]['as craftBenchProbe'] = ['class' => ProbeBehavior::class];
            }
        } elseif ($level === 'root') {
            if ($vector === 'on') {
                $layout['on init'] = ProbeHandler::class . '::handle';
            } else {
                $layout['as craftBenchProbe'] = ['class' => ProbeBehavior::class];
            }
        }

        return $layout;
    }

    /** A legitimate element config with the values the layout designer supports. */
    public static function legitElement(string $uid): array
    {
        return [
            'type' => \craft\fieldlayoutelements\Template::class,
            'template' => '_layout-elements/info',
            'width' => 50,
            'uid' => $uid,
            'userCondition' => [
                'class' => UserCondition::class,
                'conditionRules' => [
                    ['class' => AdminConditionRule::class, 'value' => true],
                ],
            ],
            'elementCondition' => [
                'class' => \craft\elements\conditions\entries\EntryCondition::class,
                'conditionRules' => [
                    ['class' => IdConditionRule::class, 'value' => 1],
                ],
            ],
        ];
    }

    public static function legitLayout(bool $stringElements = false): array
    {
        $uid = StringHelper::UUID();
        $elements = [self::legitElement($uid)];
        if ($stringElements) {
            $elements = Json::encode($elements);
        }
        return [
            'tabs' => [[
                'name' => 'Content',
                'elements' => $elements,
            ]],
        ];
    }

    /**
     * Posts a field layout through the control panel's entry-type save action.
     *
     * @return \Throwable|null the exception the action raised, if any
     */
    public static function postEntryTypeLayout(array $layoutConfig, ?string $handle = null): ?\Throwable
    {
        $_SERVER['REQUEST_METHOD'] = 'POST';

        $handle ??= 'craftBench' . substr(StringHelper::UUID(), 0, 8);
        self::$lastEntryTypeHandle = $handle;

        $request = new \craft\web\Request();
        $request->setBodyParams([
            'sectionId' => self::$section->id,
            'name' => 'CraftBench ' . substr(StringHelper::UUID(), 0, 8),
            'handle' => $handle,
            'fieldLayout' => Json::encode($layoutConfig),
        ]);
        $request->setIsCpRequest(true);
        $request->getHeaders()->set('Accept', 'application/json');

        self::$app->set('request', $request);

        $controller = new \craft\controllers\SectionsController('sections', self::$app);

        try {
            $controller->actionSaveEntryType();
            return null;
        } catch (\Throwable $e) {
            return $e;
        }
    }

    /**
     * Runs the element index's real query-building entry point for a source.
     *
     * @return array{0: \Throwable|null, 1: mixed}
     */
    public static function elementIndexQuery(string $sourceKey): array
    {
        $request = new \craft\web\Request();
        $request->setQueryParams([
            'elementType' => Entry::class,
            'source' => $sourceKey,
        ]);
        $request->setBodyParams([]);
        $request->setIsCpRequest(true);
        $request->getHeaders()->set('Accept', 'application/json');

        self::$app->set('request', $request);

        $controller = new \craft\controllers\ElementIndexesController('element-indexes', self::$app);
        $action = new \yii\base\Action('get-elements', $controller);

        try {
            $controller->beforeAction($action);
            return [null, $controller->getElementQuery()];
        } catch (\Throwable $e) {
            return [$e, null];
        }
    }

    public static function setProjectConfig(string $path, mixed $value): void
    {
        self::$app->getProjectConfig()->set($path, $value, 'CraftBench test');
    }

    public static function setElementSources(array $sources): void
    {
        self::setProjectConfig(ProjectConfig::PATH_ELEMENT_SOURCES . '.' . Entry::class, $sources);
    }

    public static function nativeSource(array $criteria): array
    {
        return [
            'type' => \craft\services\ElementSources::TYPE_NATIVE,
            'key' => self::sourceKey(),
            'criteria' => $criteria,
        ];
    }
}
