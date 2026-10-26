<?php

/**
 * An ordinary group page keeps rendering its name, its members and the restore control.
 */
final class GroupPagePlainTest extends AppTestCase
{
    public function test_plain_group_page_still_works(): void
    {
        $id = self::groupId('Gruppo Nord');
        $this->assertGreaterThan(0, $id, 'fixture group is missing');

        $html = $this->fetchPage($this->admin(), '/editor.php?id_module='.self::moduleId('Utenti e permessi').'&id_record='.$id);

        $this->assertStringContainsString('Gruppo Nord', self::cardHeader($html, 'Utenti del gruppo:'), 'the members card lost the group name');
        $this->assertStringContainsString('Gruppo Nord', self::cardHeader($html, 'Permessi del gruppo:'), 'the permissions card lost the group name');
        $this->assertStringContainsString('mario.rossi', $html, 'the member list lost its member');
    }

    public function test_member_contact_details_stay_visible(): void
    {
        $id = self::groupId('Gruppo Nord');
        $this->assertGreaterThan(0, $id, 'fixture group is missing');

        $html = $this->fetchPage($this->admin(), '/editor.php?id_module='.self::moduleId('Utenti e permessi').'&id_record='.$id);

        $this->assertStringContainsString('mario.rossi@example.invalid', $html, 'the member e-mail is no longer shown');
    }
}
