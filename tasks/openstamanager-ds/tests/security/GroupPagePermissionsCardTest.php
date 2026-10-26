<?php

/**
 * The permissions card title of the same page carries the same stored name, through a
 * different value.
 */
final class GroupPagePermissionsCardTest extends AppTestCase
{
    public function test_group_name_is_text_in_the_permissions_card(): void
    {
        $id = self::groupId('Beta <img src="x" alt="x" />');
        $this->assertGreaterThan(0, $id, 'fixture group is missing');

        $html = $this->fetchPage($this->admin(), '/editor.php?id_module='.self::moduleId('Utenti e permessi').'&id_record='.$id);

        $card = self::cardHeader($html, 'Permessi del gruppo:');
        $this->assertNotSame('', $card, 'the permissions card was not rendered');
        $this->assertStringNotContainsString('alt="x"', $card, 'the stored group name was emitted as markup');
    }
}
