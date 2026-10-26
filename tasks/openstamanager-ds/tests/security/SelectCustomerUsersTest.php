<?php

/**
 * The customer/user picker builds its suggestions by hand from stored names.
 */
final class SelectCustomerUsersTest extends AppTestCase
{
    public function test_customer_names_are_text(): void
    {
        $data = $this->fetchSelect($this->admin(), 'op=anagrafiche_utenti');
        $texts = self::displayTexts($data);

        $this->assertNotEmpty($texts, 'the picker returned no suggestions');
        foreach ($texts as $text) {
            $this->assertStringNotContainsString('alt="x"', $text, 'a stored customer name was emitted as markup');
        }
    }
}
