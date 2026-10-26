<?php
/**
 * Legitimate creation and attribution must keep working: an actor can create records for
 * themselves and for their reports, the all-user write permission keeps working, and edits
 * that leave ownership inside the hierarchy are accepted.
 */
class AttributionLegitTest extends ApiTestCase
{
    public function testManagerCreatesLeaveForSelf(): void
    {
        $r = $this->api('POST', '/holidays', self::KEY_MANAGER, array(
            'fk_user' => self::UID_MANAGER,
            'fk_type' => 3,
            'date_debut' => date('Y-m-d', strtotime('+40 days')),
            'date_fin' => date('Y-m-d', strtotime('+41 days')),
            'fk_validator' => self::UID_ADMIN,
            'description' => 'cwe-legit-leave-self',
        ));
        $this->assertAllowed($r, 'manager creating a leave for themselves');
        $this->assertSame(1, $this->countRows("SELECT COUNT(*) FROM llx_holiday WHERE description = 'cwe-legit-leave-self' AND fk_user = ".self::UID_MANAGER));
    }

    public function testManagerCreatesLeaveForSubordinate(): void
    {
        $r = $this->api('POST', '/holidays', self::KEY_MANAGER, array(
            'fk_user' => self::UID_SUB,
            'fk_type' => 3,
            'date_debut' => date('Y-m-d', strtotime('+42 days')),
            'date_fin' => date('Y-m-d', strtotime('+43 days')),
            'fk_validator' => self::UID_MANAGER,
            'description' => 'cwe-legit-leave-sub',
        ));
        $this->assertAllowed($r, 'manager creating a leave for a subordinate');
        $this->assertSame(1, $this->countRows("SELECT COUNT(*) FROM llx_holiday WHERE description = 'cwe-legit-leave-sub' AND fk_user = ".self::UID_SUB));
    }

    public function testAllUserWritePermissionCreatesLeaveForAnyone(): void
    {
        $r = $this->api('POST', '/holidays', self::KEY_WRITER, array(
            'fk_user' => self::UID_OUT,
            'fk_type' => 3,
            'date_debut' => date('Y-m-d', strtotime('+44 days')),
            'date_fin' => date('Y-m-d', strtotime('+45 days')),
            'fk_validator' => self::UID_WRITER,
            'description' => 'cwe-legit-leave-all',
        ));
        $this->assertAllowed($r, 'all-user write permission creating a leave');
        $this->assertSame(1, $this->countRows("SELECT COUNT(*) FROM llx_holiday WHERE description = 'cwe-legit-leave-all' AND fk_user = ".self::UID_OUT));
    }

    public function testManagerCreatesExpenseReportForSelf(): void
    {
        $r = $this->api('POST', '/expensereports', self::KEY_MANAGER, array(
            'fk_user_author' => self::UID_MANAGER,
            'date_debut' => date('Y-m-d', strtotime('-3 days')),
            'date_fin' => date('Y-m-d', strtotime('-2 days')),
            'note_public' => 'cwe-legit-report-self',
        ));
        $this->assertAllowed($r, 'manager creating a report for themselves');
        $this->assertSame(1, $this->countRows("SELECT COUNT(*) FROM llx_expensereport WHERE note_public = 'cwe-legit-report-self' AND fk_user_author = ".self::UID_MANAGER));
    }

    public function testManagerCreatesExpenseReportForSubordinate(): void
    {
        $r = $this->api('POST', '/expensereports', self::KEY_MANAGER, array(
            'fk_user_author' => self::UID_SUB,
            'date_debut' => date('Y-m-d', strtotime('-4 days')),
            'date_fin' => date('Y-m-d', strtotime('-3 days')),
            'note_public' => 'cwe-legit-report-sub',
        ));
        $this->assertAllowed($r, 'manager creating a report for a subordinate');
        $this->assertSame(1, $this->countRows("SELECT COUNT(*) FROM llx_expensereport WHERE note_public = 'cwe-legit-report-sub' AND fk_user_author = ".self::UID_SUB));
    }

    public function testAllUserWritePermissionCreatesReportForAnyone(): void
    {
        $r = $this->api('POST', '/expensereports', self::KEY_WRITER, array(
            'fk_user_author' => self::UID_OUT,
            'date_debut' => date('Y-m-d', strtotime('-5 days')),
            'date_fin' => date('Y-m-d', strtotime('-4 days')),
            'note_public' => 'cwe-legit-report-all',
        ));
        $this->assertAllowed($r, 'all-user write permission creating a report');
        $this->assertSame(1, $this->countRows("SELECT COUNT(*) FROM llx_expensereport WHERE note_public = 'cwe-legit-report-all' AND fk_user_author = ".self::UID_OUT));
    }

    public function testManagerEditsSubordinateLeaveWithoutChangingOwner(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-FA-L', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('PUT', '/holidays/'.$id, self::KEY_MANAGER, array('fk_user' => self::UID_SUB, 'description' => 'cwe-legit-edit'));
        $this->assertAllowed($r, 'manager editing a subordinate leave');
        $this->assertSame('cwe-legit-edit', $this->row('llx_holiday', $id)['description']);
    }

    public function testManagerEditsSubordinateReportWithoutChangingOwner(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-FA-E', 'fk_user_author' => self::UID_SUB, 'note_public' => 'old'));
        $r = $this->api('PUT', '/expensereports/'.$id, self::KEY_MANAGER, array('fk_user_author' => self::UID_SUB, 'note_public' => 'cwe-legit-report-edit'));
        $this->assertAllowed($r, 'manager editing a subordinate report');
        $this->assertSame('cwe-legit-report-edit', $this->row('llx_expensereport', $id)['note_public']);
    }
}
