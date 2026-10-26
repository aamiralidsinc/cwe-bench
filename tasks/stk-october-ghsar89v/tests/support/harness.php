<?php

use Cms\Classes\Controller;
use Cms\Classes\Theme;

/**
 * Shared setup for the hidden suites.
 *
 * Every case gets its own temporary theme under a temporary themes root, so no two cases share a
 * compiled-template entry, a URL-map cache entry or a model instance; the previous themes path is
 * restored when the case ends. Cases drive the product through the same entry point the project's
 * own CMS tests use: a Theme, a Cms\Classes\Controller and Controller::run() for a URL.
 */
abstract class CmsHiddenCase extends TestCase
{
    /** @var string */
    protected $themesRoot;

    /** @var string */
    protected $themeName;

    /** @var string */
    protected $previousThemesPath;

    public function setUp()
    {
        parent::setUp();

        // The model layer binds its save hooks once per process; a fresh application (one per test)
        // would otherwise reuse the first application's "already booted" marker and silently lose
        // them. Reset the markers so this test's application binds them again.
        self::resetModelBootState();

        Config::set('cms.enableSafeMode', true);

        $this->previousThemesPath = app('path.themes');
        $this->themesRoot = sys_get_temp_dir() . '/oct-cms-' . bin2hex(random_bytes(8));
        $this->themeName = 'theme' . bin2hex(random_bytes(4));

        $dir = $this->themeDir();
        mkdir($dir . '/pages', 0777, true);
        mkdir($dir . '/layouts', 0777, true);
        mkdir($dir . '/partials', 0777, true);
        file_put_contents($dir . '/theme.yaml', "name: " . $this->themeName . "\n");

        App::setThemesPath($this->themesRoot);
    }

    public function tearDown()
    {
        App::setThemesPath($this->previousThemesPath);
        self::removeDirectory($this->themesRoot);
        parent::tearDown();
    }

    //
    // Fixtures
    //

    protected function themeDir()
    {
        return $this->themesRoot . '/' . $this->themeName;
    }

    protected function pagePath($name)
    {
        return $this->themeDir() . '/pages/' . $name . '.htm';
    }

    /**
     * Writes a CMS page file. $settings is the INI section (always contains the url),
     * $code an optional PHP code section, $markup the template body.
     */
    protected function writePage($name, $markup, $settings = null, $code = '')
    {
        if ($settings === null) {
            $settings = 'url = "/"';
        }

        $sections = [$settings];
        if (strlen(trim($code))) {
            $sections[] = $code;
        }
        $sections[] = $markup;

        file_put_contents($this->pagePath($name), implode("\n==\n", $sections));
        clearstatcache();
    }

    protected function writeLayout($name, $markup, $settings = '')
    {
        $content = strlen(trim($settings)) ? $settings . "\n==\n" . $markup : $markup;
        file_put_contents($this->themeDir() . '/layouts/' . $name . '.htm', $content);
        clearstatcache();
    }

    protected function writePartial($name, $markup)
    {
        file_put_contents($this->themeDir() . '/partials/' . $name . '.htm', $markup);
        clearstatcache();
    }

    //
    // Driving the product
    //

    /**
     * Renders $url through the CMS front end. Returns ['output' => string, 'error' => Throwable|null];
     * every error is captured, so a case never depends on one particular failure form.
     */
    protected function render($url = '/')
    {
        try {
            $theme = Theme::load($this->themeName);
            $controller = new Controller($theme);
            $result = $controller->run($url);
            $output = is_object($result) ? $result->getContent() : (string) $result;
            return ['output' => $output, 'error' => null];
        }
        catch (\Throwable $e) {
            return ['output' => '', 'error' => $e];
        }
    }

    /**
     * Renders $url in a separate PHP process, the way a later request would. The compiled-template
     * cache is per process and keyed by file path, so a second request for a template that changed
     * on disk is only faithful in a fresh process.
     */
    protected function renderInFreshProcess($url = '/')
    {
        $command = escapeshellarg(PHP_BINARY)
            . ' ' . escapeshellarg(__DIR__ . '/render.php')
            . ' ' . escapeshellarg(base_path())
            . ' ' . escapeshellarg($this->themesRoot)
            . ' ' . escapeshellarg($this->themeName)
            . ' ' . escapeshellarg($url)
            . ' 2>&1';

        return (string) shell_exec($command);
    }

    //
    // Markers
    //

    /** A path no legitimate render would ever write. */
    protected function markerPath()
    {
        return sys_get_temp_dir() . '/oct-marker-' . bin2hex(random_bytes(8));
    }

    /**
     * The attack ran if the marker exists. This is the side effect itself: it holds for a refusal
     * by any layer and never depends on one particular status, message or error type.
     */
    protected function assertAttackDidNotRun($marker)
    {
        clearstatcache();
        $this->assertFileNotExists($marker, 'template content executed PHP');
    }

    protected static function removeDirectory($dir)
    {
        if (!is_dir($dir)) {
            return;
        }
        foreach (scandir($dir) as $entry) {
            if ($entry === '.' || $entry === '..') {
                continue;
            }
            $path = $dir . '/' . $entry;
            is_dir($path) ? self::removeDirectory($path) : @unlink($path);
        }
        @rmdir($dir);
    }

    /**
     * Clears the model layer's per-process "booted" / "events bound" markers. Each test runs in a
     * new application instance, but those markers are static, so without this the save hooks bound
     * for the first application are not bound for the next one.
     */
    protected static function resetModelBootState()
    {
        $class = new \ReflectionClass(\October\Rain\Halcyon\Model::class);
        foreach (['booted', 'eventsBooted'] as $name) {
            if (!$class->hasProperty($name)) {
                continue;
            }
            $property = $class->getProperty($name);
            $property->setAccessible(true);
            $property->setValue(null, []);
        }
    }
}
