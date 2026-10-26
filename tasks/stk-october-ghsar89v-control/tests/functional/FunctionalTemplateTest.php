<?php

/**
 * Every template feature that works today keeps working: settings values, property access, method
 * calls the product itself provides, filters, loops, conditionals and partials.
 */
class FunctionalTemplateTest extends CmsHiddenCase
{
    public function test_settings_properties_and_expressions_still_render()
    {
        $this->writePage('index', implode("\n", [
            "<h1>{{ this.page.title }}</h1>",
            "<p>{{ this.controller.themeUrl() }}</p>",
            "{% if this.page.title == 'Welcome' %}CONDITION-OK{% endif %}",
            "{% for i in [1, 2, 3] %}{{ i }}{% endfor %}",
            "{{ 'abc'|upper }}",
        ]), "url = \"/\"\ntitle = \"Welcome\"");

        $result = $this->render('/');

        $this->assertNull($result['error'], 'a legitimate template failed to render');
        $this->assertContains('<h1>Welcome</h1>', $result['output']);
        $this->assertContains('CONDITION-OK', $result['output']);
        $this->assertContains('123', $result['output']);
        $this->assertContains('ABC', $result['output']);
    }

    public function test_partials_still_render()
    {
        $this->writePartial('greeting', '<span>{{ this.page.title }}</span>');
        $this->writePage('index', "{% partial 'greeting' %}", "url = \"/\"\ntitle = \"Hello\"");

        $result = $this->render('/');

        $this->assertNull($result['error'], 'a legitimate template failed to render');
        $this->assertContains('<span>Hello</span>', $result['output']);
    }
}
