<?php

/**
 * The stored group name also reaches a confirmation message carried in an attribute of the
 * restore-permissions control. Quotes inside the value must not end the attribute.
 */
final class GroupPageAttributeTest extends AppTestCase
{
    public function test_restore_message_keeps_the_group_name_as_text(): void
    {
        $id = self::groupId('Gamma " onmouseover="alert(1)');
        $this->assertGreaterThan(0, $id, 'fixture group is missing');

        $html = $this->fetchPage($this->admin(), '/editor.php?id_module='.self::moduleId('Utenti e permessi').'&id_record='.$id);

        $this->assertStringContainsString('Gamma', $html, 'the group page did not render the group');
        $this->assertStringNotContainsString('onmouseover="alert(1)', $html, 'the stored group name broke out of an attribute');
    }
}
