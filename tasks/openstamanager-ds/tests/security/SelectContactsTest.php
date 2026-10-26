<?php

/**
 * The contact picker of a customer, for an actor who may not open the contact records.
 */
final class SelectContactsTest extends AppTestCase
{
    public function test_contact_names_are_text_without_the_plugin(): void
    {
        $data = $this->fetchSelect($this->clerk(), 'op=referenti_cliente');
        $texts = self::displayTexts($data);

        $this->assertNotEmpty($texts, 'the picker returned no suggestions');
        foreach ($texts as $text) {
            $this->assertStringNotContainsString('alt="x"', $text, 'a stored contact name was emitted as markup');
        }
    }
}
