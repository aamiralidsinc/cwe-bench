<?php
/**
 * A request may not create a record for, or move a record to, a user outside the caller's
 * management hierarchy (nor name an outside user as its approver).
 */
class AttributionSecurityTest extends ApiTestCase
{
    public function testCannotCreateLeaveForOutsideUser(): void
    {
        $before = $this->countRows("SELECT COUNT(*) FROM llx_holiday WHERE description = 'cwe-created-leave-a'");
        $r = $this->api('POST', '/holidays', self::KEY_MANAGER, array(
            'fk_user' => self::UID_OUT,
            'fk_type' => 3,
            'date_debut' => date('Y-m-d', strtotime('+40 days')),
            'date_fin' => date('Y-m-d', strtotime('+41 days')),
            'fk_validator' => self::UID_MANAGER,
            'description' => 'cwe-created-leave-a',
        ));
        $this->assertBlocked($r, 'creating a leave for an outside user');
        $after = $this->countRows("SELECT COUNT(*) FROM llx_holiday WHERE description = 'cwe-created-leave-a'");
        $this->assertSame($before, $after);
    }

    public function testCannotMoveALeaveToAnOutsideUser(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-ATTR-L', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('PUT', '/holidays/'.$id, self::KEY_MANAGER, array('fk_user' => self::UID_OUT));
        $this->assertBlocked($r, 'moving a leave to an outside user');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame((string) self::UID_SUB, (string) $row['fk_user']);
    }

    public function testCannotNameAnOutsideApprover(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-ATTR-V', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('PUT', '/holidays/'.$id, self::KEY_MANAGER, array('fk_validator' => self::UID_OUT));
        $this->assertBlocked($r, 'naming an outside approver');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame((string) self::UID_MANAGER, (string) $row['fk_validator']);
    }

    public function testCannotCreateExpenseReportForOutsideUser(): void
    {
        $before = $this->countRows("SELECT COUNT(*) FROM llx_expensereport WHERE note_public = 'cwe-created-report-a'");
        $r = $this->api('POST', '/expensereports', self::KEY_MANAGER, array(
            'fk_user_author' => self::UID_OUT,
            'date_debut' => date('Y-m-d', strtotime('-3 days')),
            'date_fin' => date('Y-m-d', strtotime('-2 days')),
            'note_public' => 'cwe-created-report-a',
        ));
        $this->assertBlocked($r, 'creating an expense report for an outside user');
        $after = $this->countRows("SELECT COUNT(*) FROM llx_expensereport WHERE note_public = 'cwe-created-report-a'");
        $this->assertSame($before, $after);
    }

    public function testCannotMoveAnExpenseReportToAnOutsideUser(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-ATTR-E', 'fk_user_author' => self::UID_SUB));
        $r = $this->api('PUT', '/expensereports/'.$id, self::KEY_MANAGER, array('fk_user_author' => self::UID_OUT));
        $this->assertBlocked($r, 'moving an expense report to an outside user');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame((string) self::UID_SUB, (string) $row['fk_user_author']);
    }
}
