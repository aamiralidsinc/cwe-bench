<?php

/**
 * Search answers keep their select2 shape and their ordinary values.
 */
final class SelectPlainTest extends AppTestCase
{
    public function test_group_search_returns_selectable_items(): void
    {
        $data = $this->fetchSelect($this->admin(), 'op=gruppi');

        $found = false;
        foreach ($data['results'] ?? [] as $item) {
            if (isset($item['id'], $item['text']) && (int) $item['id'] === self::groupId('Gruppo Nord') && str_contains($item['text'], 'Gruppo Nord')) {
                $found = true;
            }
        }
        $this->assertTrue($found, 'the group search no longer returns the group');
    }

    public function test_customer_user_search_returns_optgroups_and_children(): void
    {
        $data = $this->fetchSelect($this->admin(), 'op=anagrafiche_utenti');

        $found = false;
        foreach ($data['results'] ?? [] as $item) {
            foreach ($item['children'] ?? [] as $child) {
                if (isset($child['id'], $child['text']) && (int) $child['id'] === 302 && str_contains($child['text'], 'Beta Service')) {
                    $found = true;
                }
            }
        }
        $this->assertTrue($found, 'the customer picker no longer returns a customer inside its group');
    }

    public function test_user_search_returns_the_display_name(): void
    {
        $texts = implode("\n", self::displayTexts($this->fetchSelect($this->admin(), 'op=utenti')));
        $this->assertStringContainsString('mario.rossi', $texts, 'the user picker lost a user');
    }

    public function test_country_search_returns_the_list(): void
    {
        $texts = implode("\n", self::displayTexts($this->fetchSelect($this->admin(), 'op=nazioni')));
        $this->assertStringContainsString('Italia', $texts, 'the country picker lost its countries');
    }

    public function test_service_type_search_returns_the_title(): void
    {
        $texts = implode("\n", self::displayTexts($this->fetchSelect($this->admin(), 'op=tipiintervento')));
        $this->assertStringContainsString('Generico', $texts, 'the service-type picker lost its types');
    }
}
