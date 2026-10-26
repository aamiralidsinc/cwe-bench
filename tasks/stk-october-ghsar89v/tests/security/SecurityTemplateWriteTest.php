<?php

/**
 * A template expression can reach the storage layer behind the page object. Writing a PHP code
 * section into the template's own file means the next request reads it back and runs it, so the
 * check has to hold for where the content ends up, not only for what a render does right now.
 */
class SecurityTemplateWriteTest extends CmsHiddenCase
{
    public function test_a_template_cannot_store_an_executable_code_section()
    {
        $marker = $this->markerPath();
        $code = "function onStart() { file_put_contents(" . var_export($marker, true) . ", 'x'); }";

        $this->writePage('index', implode('', [
            "{% set _ = this.page.newQuery().update({'code': " . var_export($code, true) . "}) %}",
            "rendered",
        ]));

        $this->render('/');

        // A later request: the compiled-template cache is per process, so the changed file has to
        // be read by a new process for this to say anything about what was stored.
        $this->bumpMtime($this->pagePath('index'));
        $this->renderInFreshProcess('/');

        $this->assertAttackDidNotRun($marker);
    }

    private function bumpMtime($path)
    {
        if (is_file($path)) {
            touch($path, time() + 5);
            clearstatcache();
        }
    }
}
