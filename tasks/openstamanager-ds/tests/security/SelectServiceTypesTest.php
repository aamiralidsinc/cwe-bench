<?php

/**
 * The service-type picker is built by another module and fills its suggestions by hand.
 */
final class SelectServiceTypesTest extends AppTestCase
{
    public function test_service_type_titles_are_text(): void
    {
        $data = $this->fetchSelect($this->clerk(), 'op=tipiintervento');
        $texts = self::displayTexts($data);

        $this->assertNotEmpty($texts, 'the picker returned no suggestions');
        foreach ($texts as $text) {
            $this->assertStringNotContainsString('alt="x"', $text, 'a stored service-type title was emitted as markup');
        }
    }
}
