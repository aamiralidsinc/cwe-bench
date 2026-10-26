<?php

/**
 * The group page hands the stored group name to a page script. A quote in the value must not
 * end the script string.
 */
final class GroupPageScriptTest extends AppTestCase
{
    public function test_group_name_cannot_leave_the_script_string(): void
    {
        $id = self::groupId('Delta\';window.__osmProbe=1;//');
        $this->assertGreaterThan(0, $id, 'fixture group is missing');

        $html = $this->fetchPage($this->admin(), '/editor.php?id_module='.self::moduleId('Utenti e permessi').'&id_record='.$id);

        $this->assertStringContainsString('Delta', $html, 'the group page did not render the group');
        $this->assertStringNotContainsString('\';window.__osmProbe=1', $html, 'the stored group name broke out of the page script');
    }
}
