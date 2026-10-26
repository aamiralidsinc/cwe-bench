<?php

/**
 * Safe mode promises that editing template content is not a way to run PHP. A template expression
 * can register a callable on the objects a template can reach and then invoke it.
 */
class SecurityDynamicRegistrationTest extends CmsHiddenCase
{
    public function test_dynamic_method_registered_from_a_page_does_not_run_php()
    {
        $marker = $this->markerPath();
        $this->writePage('index', implode('', [
            "{% set _ = this.page.addDynamicMethod('run', 'file_put_contents') %}",
            "{{ this.page.run(" . var_export($marker, true) . ", 'x') }}",
            "rendered",
        ]));

        $result = $this->render('/');

        $this->assertAttackDidNotRun($marker);
    }

    public function test_dynamic_method_spelled_in_mixed_case_does_not_run_php()
    {
        $marker = $this->markerPath();
        $this->writePage('index', implode('', [
            "{% set _ = this.page.AdDDyNamiCMethod('run', 'file_put_contents') %}",
            "{{ this.page.run(" . var_export($marker, true) . ", 'x') }}",
            "rendered",
        ]));

        $result = $this->render('/');

        $this->assertAttackDidNotRun($marker);
    }

    public function test_dynamic_method_reached_through_the_attribute_helper_does_not_run_php()
    {
        $marker = $this->markerPath();
        $this->writePage('index', implode('', [
            "{% set _ = attribute(this.page, 'addDynamicMethod', ['run', 'file_put_contents']) %}",
            "{{ this.page.run(" . var_export($marker, true) . ", 'x') }}",
            "rendered",
        ]));

        $result = $this->render('/');

        $this->assertAttackDidNotRun($marker);
    }

    public function test_dynamic_method_registered_from_a_layout_does_not_run_php()
    {
        $marker = $this->markerPath();
        $this->writeLayout('main', implode('', [
            "{% set _ = this.layout.addDynamicMethod('run', 'file_put_contents') %}",
            "{{ this.layout.run(" . var_export($marker, true) . ", 'x') }}",
            "{{ page() }}",
        ]));
        $this->writePage('index', 'rendered', "url = \"/\"\nlayout = \"main\"");

        $result = $this->render('/');

        $this->assertAttackDidNotRun($marker);
    }
}
