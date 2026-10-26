<?php
/**
 * Legitimate list use must keep working: a manager still sees the reports of their reports,
 * the all-user read permission still sees everyone, and the user filter still filters.
 */
class ListLegitTest extends ApiTestCase
{
    public function testManagerSeesOwnAndSubordinateReports(): void
    {
        $own = $this->mkExpense(array('ref' => 'CWETEST-FL-OWN', 'fk_user_author' => self::UID_MANAGER));
        $sub = $this->mkExpense(array('ref' => 'CWETEST-FL-SUB', 'fk_user_author' => self::UID_SUB));
        $r = $this->api('GET', '/expensereports', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager listing expense reports');
        $this->assertBodyHas($r, 'CWETEST-FL-OWN');
        $this->assertBodyHas($r, 'CWETEST-FL-SUB');
    }

    public function testAllUserPermissionSeesEverybody(): void
    {
        $outside = $this->mkExpense(array('ref' => 'CWETEST-FL-ALL', 'fk_user_author' => self::UID_OUT));
        $r = $this->api('GET', '/expensereports', self::KEY_ALL);
        $this->assertAllowed($r, 'all-user permission listing expense reports');
        $this->assertBodyHas($r, 'CWETEST-FL-ALL');
    }

    public function testUserFilterStillSelectsOneUser(): void
    {
        $own = $this->mkExpense(array('ref' => 'CWETEST-FL-FO', 'fk_user_author' => self::UID_MANAGER));
        $sub = $this->mkExpense(array('ref' => 'CWETEST-FL-FS', 'fk_user_author' => self::UID_SUB));
        $r = $this->api('GET', '/expensereports?user_ids='.self::UID_SUB, self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager filtering by a subordinate');
        $this->assertBodyHas($r, 'CWETEST-FL-FS');
        $this->assertBodyLacks($r, 'CWETEST-FL-FO');
    }

    public function testUserFilterSelectsTheCaller(): void
    {
        $own = $this->mkExpense(array('ref' => 'CWETEST-FL-ME', 'fk_user_author' => self::UID_MANAGER));
        $r = $this->api('GET', '/expensereports?user_ids='.self::UID_MANAGER, self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager filtering by themselves');
        $this->assertBodyHas($r, 'CWETEST-FL-ME');
    }
}
