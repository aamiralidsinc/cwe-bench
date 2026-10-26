<?php

/**
 * The same page lists the members of the group: their own stored values must arrive as text
 * too.
 */
final class GroupPageMemberTableTest extends AppTestCase
{
    public function test_member_username_is_text(): void
    {
        $id = self::groupId('Beta <img src="x" alt="x" />');
        $this->assertGreaterThan(0, $id, 'fixture group is missing');

        $html = $this->fetchPage($this->admin(), '/editor.php?id_module='.self::moduleId('Utenti e permessi').'&id_record='.$id);

        $this->assertStringContainsString('eve.ops@example.invalid', $html, 'the member row was not rendered');
        $this->assertStringNotContainsString('<b>ops</b>', $html, 'the stored member name was emitted as markup');
    }
}
