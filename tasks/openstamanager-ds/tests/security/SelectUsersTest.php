<?php

/**
 * The user picker builds its display name from the linked customer record and the username.
 */
final class SelectUsersTest extends AppTestCase
{
    public function test_user_display_names_are_text(): void
    {
        $data = $this->fetchSelect($this->admin(), 'op=utenti');
        $texts = self::displayTexts($data);

        $this->assertNotEmpty($texts, 'the picker returned no suggestions');
        foreach ($texts as $text) {
            $this->assertStringNotContainsString('alt="x"', $text, 'a stored user name was emitted as markup');
        }
    }
}
