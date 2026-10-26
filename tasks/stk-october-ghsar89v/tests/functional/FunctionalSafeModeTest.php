<?php

use Cms\Classes\Page;
use Cms\Classes\Theme;

/**
 * Safe mode's own, older guarantee keeps working: while it is on, a template saved through the
 * object model cannot gain a PHP code section.
 */
class FunctionalSafeModeTest extends CmsHiddenCase
{
    public function test_safe_mode_still_refuses_a_new_code_section()
    {
        $theme = Theme::load($this->themeName);

        $page = Page::inTheme($theme);
        $page->fileName = 'created.htm';
        $page->url = '/created';
        $page->title = 'Created';
        $page->markup = '<p>hello</p>';
        $page->code = "function onStart() { return 1; }";

        $refused = false;
        try {
            $page->save();
        }
        catch (\Throwable $e) {
            $refused = true;
        }

        $this->assertTrue($refused, 'saving a code section under safe mode was not refused');
        $this->assertFileNotExists($theme->getPath() . '/pages/created.htm');
    }

    public function test_safe_mode_still_allows_saving_markup_without_code()
    {
        $theme = Theme::load($this->themeName);

        $page = Page::inTheme($theme);
        $page->fileName = 'created.htm';
        $page->url = '/created';
        $page->title = 'Created';
        $page->markup = '<p>hello</p>';
        $page->save();

        $this->assertFileExists($theme->getPath() . '/pages/created.htm');
        $this->assertContains('<p>hello</p>', file_get_contents($theme->getPath() . '/pages/created.htm'));
    }
}
