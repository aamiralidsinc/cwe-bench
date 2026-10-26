<?php

/**
 * The customer picker for an actor who may not open customer records: the suggestion must
 * still carry the stored name as text.
 */
final class SelectCustomersFallbackTest extends AppTestCase
{
    public function test_customer_names_are_text_without_the_record_module(): void
    {
        $data = $this->fetchSelect($this->clerk(), 'op=clienti');
        $texts = self::displayTexts($data);

        $this->assertNotEmpty($texts, 'the picker returned no suggestions');
        foreach ($texts as $text) {
            $this->assertStringNotContainsString('alt="x"', $text, 'a stored customer name was emitted as markup');
        }
    }
}
