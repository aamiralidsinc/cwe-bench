<?php

/**
 * Code sections that a developer put in a theme keep working exactly as today: the page life cycle
 * runs them, the event mechanism is usable from them, and so is the storage layer behind a page.
 * None of that is template content, so nothing about safe mode changes it.
 */
class FunctionalCodeSectionTest extends CmsHiddenCase
{
    public function test_a_deployed_code_section_still_runs()
    {
        $this->writePage(
            'index',
            '{{ greeting }}',
            'url = "/"',
            "function onStart() {\n    \$this['greeting'] = 'code-ran';\n}"
        );

        $result = $this->render('/');

        $this->assertNull($result['error'], 'a deployed code section failed to run');
        $this->assertContains('code-ran', $result['output']);
    }

    public function test_event_binding_from_php_still_works()
    {
        $this->writePage(
            'index',
            '{{ greeting }}',
            'url = "/"',
            "function onStart() {\n"
            . "    \$this->page->bindEvent('greet', 'strtoupper');\n"
            . "    \$this['greeting'] = \$this->page->fireEvent('greet', ['hello'], true);\n"
            . "}"
        );

        $result = $this->render('/');

        $this->assertNull($result['error'], 'event binding from a code section stopped working');
        $this->assertContains('HELLO', $result['output']);
    }

    public function test_the_page_storage_api_is_still_usable_from_php()
    {
        $this->writePage(
            'index',
            '{{ total }}',
            'url = "/"',
            "function onStart() {\n    \$this['total'] = \$this->page->newQuery()->get()->count();\n}"
        );

        $result = $this->render('/');

        $this->assertNull($result['error'], 'the page storage API stopped working from PHP');
        $this->assertContains('1', $result['output']);
    }
}
