<?php

/**
 * The product still builds its own links around a stored name: a permitted user gets a real
 * link to the record from the search answer, both for a module record and for a plugin.
 */
final class SelectLinkTest extends AppTestCase
{
    public function test_customer_search_returns_a_record_link(): void
    {
        $moduleId = self::moduleId('Anagrafiche');
        $texts = implode("\n", self::displayTexts($this->fetchSelect($this->admin(), 'op=clienti')));

        $this->assertStringContainsString('Beta Service', $texts, 'the customer is no longer suggested');
        $this->assertStringContainsString('<a href=', $texts, 'the record link is gone');
        $this->assertStringContainsString('id_module='.$moduleId, $texts, 'the record link no longer points at the module');
        $this->assertStringContainsString('id_record=302', $texts, 'the record link no longer points at the record');
    }

    public function test_contact_search_returns_a_plugin_link(): void
    {
        $moduleId = self::moduleId('Anagrafiche');
        $texts = implode("\n", self::displayTexts($this->fetchSelect($this->admin(), 'op=referenti_cliente')));

        $this->assertStringContainsString('Sig. Bianchi', $texts, 'the contact is no longer suggested');
        $this->assertStringContainsString('<a href=', $texts, 'the contact link is gone');
        $this->assertStringContainsString('id_record=502', $texts, 'the contact link no longer points at the contact');
        $this->assertStringContainsString('id_module='.$moduleId, $texts, 'the contact link no longer points at the module');
    }
}
