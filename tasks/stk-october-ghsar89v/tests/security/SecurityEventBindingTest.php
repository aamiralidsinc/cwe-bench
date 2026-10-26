<?php

/**
 * The event mechanism is another way for a template expression to reach an attacker-chosen
 * callable: bind a listener, then fire the event with the arguments.
 */
class SecurityEventBindingTest extends CmsHiddenCase
{
    public function test_event_bound_on_a_page_does_not_run_php()
    {
        $marker = $this->markerPath();
        $this->writePage('index', implode('', [
            "{% set _ = this.page.bindEvent('go', 'file_put_contents') %}",
            "{{ this.page.fireEvent('go', [" . var_export($marker, true) . ", 'x']) }}",
            "rendered",
        ]));

        $result = $this->render('/');

        $this->assertAttackDidNotRun($marker);
    }

    public function test_event_bound_on_the_page_controller_does_not_run_php()
    {
        $marker = $this->markerPath();
        $this->writePage('index', implode('', [
            "{% set _ = this.controller.bindEvent('go', 'file_put_contents') %}",
            "{{ this.controller.fireEvent('go', [" . var_export($marker, true) . ", 'x']) }}",
            "rendered",
        ]));

        $result = $this->render('/');

        $this->assertAttackDidNotRun($marker);
    }

    public function test_one_shot_event_bound_on_a_page_does_not_run_php()
    {
        $marker = $this->markerPath();
        $this->writePage('index', implode('', [
            "{% set _ = this.page.bindEventOnce('go', 'file_put_contents') %}",
            "{{ this.page.fireEvent('go', [" . var_export($marker, true) . ", 'x']) }}",
            "rendered",
        ]));

        $result = $this->render('/');

        $this->assertAttackDidNotRun($marker);
    }
}
