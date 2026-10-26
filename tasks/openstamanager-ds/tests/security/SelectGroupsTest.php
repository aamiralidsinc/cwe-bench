<?php

/**
 * The group picker is filled from the group titles.
 */
final class SelectGroupsTest extends AppTestCase
{
    public function test_group_titles_are_text(): void
    {
        $data = $this->fetchSelect($this->admin(), 'op=gruppi');
        $texts = self::displayTexts($data);

        $this->assertNotEmpty($texts, 'the picker returned no suggestions');
        foreach ($texts as $text) {
            $this->assertStringNotContainsString('alt="x"', $text, 'a stored group title was emitted as markup');
        }
    }
}
