<?php

/**
 * A group carries its name into the two card titles of its edit page. Whatever a user saved
 * must arrive there as text.
 */
final class GroupPageCardTitleTest extends AppTestCase
{
    public function test_group_name_is_text_in_the_members_card(): void
    {
        $id = self::groupId('Beta <img src="x" alt="x" />');
        $this->assertGreaterThan(0, $id, 'fixture group is missing');

        $html = $this->fetchPage($this->admin(), '/editor.php?id_module='.self::moduleId('Utenti e permessi').'&id_record='.$id);

        $card = self::cardHeader($html, 'Utenti del gruppo:');
        $this->assertNotSame('', $card, 'the members card was not rendered');
        $this->assertStringNotContainsString('alt="x"', $card, 'the stored group name was emitted as markup');
    }
}
