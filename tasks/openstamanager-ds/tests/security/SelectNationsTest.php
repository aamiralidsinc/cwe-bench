<?php

/**
 * A picker filled by a plain lookup table (no hand-built result array, no link around the
 * value): the stored name must still arrive as text.
 */
final class SelectNationsTest extends AppTestCase
{
    public function test_country_names_are_text(): void
    {
        $data = $this->fetchSelect($this->admin(), 'op=nazioni&search=Nazione');
        $texts = self::displayTexts($data);

        $this->assertNotEmpty($texts, 'the picker returned no suggestions');
        foreach ($texts as $text) {
            $this->assertStringNotContainsString('alt="x"', $text, 'a stored country name was emitted as markup');
        }
    }
}
