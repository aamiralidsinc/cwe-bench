<?php

namespace CweTests;

use Grav\Common\Grav;
use Grav\Common\Page\Interfaces\PageInterface;
use Grav\Common\Security;
use Grav\Common\Theme;
use Grav\Common\Twig\Twig;
use PHPUnit\Framework\TestCase;
use ReflectionClass;
use Symfony\Component\VarDumper\Cloner\VarCloner;
use Symfony\Component\VarDumper\Dumper\CliDumper;
use Symfony\Component\VarDumper\VarDumper;

/**
 * Base class for the config-exfiltration tests. Builds a fresh Grav instance,
 * seeds two marker secrets into configuration, and renders Twig through the
 * application's own Twig service — the real entry points:
 *
 *  - editor content: Twig::processPage() (a page body with Twig enabled) and
 *    Twig::processString() (an editor-derived string), both sandboxed by the
 *    application;
 *  - trusted operator Twig: Twig::processTemplateString().
 *
 * All expected values and markers are computed here in the test, never by
 * calling the product code under audit.
 */
abstract class SandboxTestCase extends TestCase
{
    /**
     * Marker secret stored under a plugin configuration subtree (the kind of
     * value — SMTP passwords, API keys — a site keeps in plugin config).
     */
    protected const SECRET_PLUGIN = 'ZZZ_PLUGIN_SECRET_7f3a1b';

    /** Marker secret stored under the security configuration subtree. */
    protected const SECRET_SECURITY = 'ZZZ_SECURITY_SECRET_9d42c0';

    /** Name of the minimal theme registered for the render. */
    protected const THEME = 'cwetheme';

    /** @var Grav */
    protected $grav;

    /** @var Twig|null */
    private $twig;

    protected function setUp(): void
    {
        parent::setUp();

        Grav::resetInstance();
        $grav = Grav::instance();
        $grav['config']->init();

        foreach (array_keys($grav['setup']->getStreams()) as $stream) {
            @stream_wrapper_unregister($stream);
        }
        $grav['streams'];

        // A minimal active theme so the Twig service can initialise headless.
        @mkdir(GRAV_ROOT . '/tmp/' . self::THEME . '/templates', 0777, true);
        $grav['locator']->addPath('theme', '', 'tmp/' . self::THEME);
        $grav['base_url'] = '';
        $grav['base_url_absolute'] = 'http://localhost';
        $grav['base_url_relative'] = '';
        $grav['config']->set('system.pages.theme', self::THEME);
        $grav['theme'] = new Theme($grav, $grav['config'], self::THEME);

        // config_access stays at its shipped default (off): sandboxed content
        // must see no configuration through any path.
        $grav['config']->set('plugins.email.mailer.smtp.password', self::SECRET_PLUGIN);
        $grav['config']->set('security.salt', self::SECRET_SECURITY);

        $this->grav = $grav;
        $this->resetSandboxPolicy();
    }

    /** Forget the memoized sandbox policy so changed config is reflected. */
    protected function resetSandboxPolicy(): void
    {
        $reflection = new ReflectionClass(Security::class);
        foreach (['twigSandboxPolicy', 'twigSandboxPolicyKey'] as $prop) {
            if ($reflection->hasProperty($prop)) {
                $p = $reflection->getProperty($prop);
                $p->setAccessible(true);
                $p->setValue(null, null);
            }
        }
    }

    /** The application's Twig service, initialised on first use. */
    protected function twig(): Twig
    {
        if ($this->twig === null) {
            $this->twig = $this->grav['twig'];
            $this->twig->init();
        }
        return $this->twig;
    }

    /** A plain page-header object, as built from a page's YAML front matter. */
    protected function header(): object
    {
        return (object) ['title' => 'Hello', 'custom_key' => 'World'];
    }

    /**
     * Run a render while capturing anything the debug dumper emits — in a web
     * request that output lands in the page, so it counts as rendered output.
     */
    protected function capture(callable $render): string
    {
        $dumped = '';
        $previous = VarDumper::setHandler(static function ($var) use (&$dumped): void {
            $dumped .= (new CliDumper())->dump((new VarCloner())->cloneVar($var), true);
        });
        try {
            $out = (string) $render();
        } finally {
            VarDumper::setHandler($previous);
        }
        return $out . $dumped;
    }

    /** Render editor-authored Twig as the body of a page with Twig enabled. */
    protected function renderPageBody(string $body): string
    {
        $page = $this->createMock(PageInterface::class);
        $page->method('header')->willReturn($this->header());
        $page->method('shouldProcess')->willReturnCallback(static fn ($what) => $what === 'twig');
        $page->method('isModule')->willReturn(false);
        $page->method('path')->willReturn(GRAV_ROOT . '/user/pages/01.cwe');
        $page->method('content')->willReturn($body);

        return $this->capture(fn () => $this->twig()->processPage($page, $body));
    }

    /** Render an editor-derived Twig string. */
    protected function renderString(string $template): string
    {
        return $this->capture(fn () => $this->twig()->processString($template, ['header' => $this->header()]));
    }

    /**
     * Render editor content through both content entry points and return what
     * reached the output, treating a thrown refusal as empty output — the
     * tests assert on what reached the page, not on how the refusal was
     * signalled.
     */
    protected function renderContent(string $template): string
    {
        $out = '';
        foreach ([[$this, 'renderPageBody'], [$this, 'renderString']] as $render) {
            try {
                $out .= "\n" . $render($template);
            } catch (\Throwable $e) {
                // refusal by exception: nothing rendered
            }
        }
        return $out;
    }

    /** Render operator-authored (trusted) Twig. */
    protected function renderTrusted(string $template): string
    {
        return $this->capture(fn () => $this->twig()->processTemplateString($template, ['header' => $this->header()]));
    }
}
