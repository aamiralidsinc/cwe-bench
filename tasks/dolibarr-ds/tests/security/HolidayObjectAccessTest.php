<?php
/**
 * Per-record leave-request endpoints must apply the management-hierarchy rule.
 * Every request here is made by the manager of user 3 against a record owned by user 4,
 * who is not in that manager's hierarchy.
 */
class HolidayObjectAccessTest extends ApiTestCase
{
    public function testGetOutsideLeaveIsRefused(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-H-GET', 'description' => 'cwe get marker'));
        $r = $this->api('GET', '/holidays/'.$id, self::KEY_MANAGER);
        $this->assertBlocked($r, 'reading an outside leave');
        $this->assertBodyLacks($r, 'cwe get marker');
        $this->assertNotNull($this->row('llx_holiday', $id));
    }

    public function testUpdateOutsideLeaveIsRefused(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-H-PUT', 'description' => 'unchanged'));
        $r = $this->api('PUT', '/holidays/'.$id, self::KEY_MANAGER, array('description' => 'cwe-put-changed'));
        $this->assertBlocked($r, 'updating an outside leave');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame('unchanged', $row['description']);
    }

    public function testDeleteOutsideLeaveIsRefused(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-H-DEL'));
        $r = $this->api('DELETE', '/holidays/'.$id, self::KEY_MANAGER);
        $this->assertBlocked($r, 'deleting an outside leave');
        $this->assertNotNull($this->row('llx_holiday', $id));
    }

    public function testValidateOutsideLeaveIsRefused(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-H-VAL', 'statut' => 1));
        $r = $this->api('POST', '/holidays/'.$id.'/validate', self::KEY_MANAGER);
        $this->assertBlocked($r, 'validating an outside leave');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame('1', (string) $row['statut']);
        $this->assertNull($row['fk_user_valid']);
    }

    public function testApproveOutsideLeaveIsRefused(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-H-APP', 'statut' => 2));
        $r = $this->api('POST', '/holidays/'.$id.'/approve', self::KEY_MANAGER);
        $this->assertBlocked($r, 'approving an outside leave');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame('2', (string) $row['statut']);
    }

    public function testCancelOutsideLeaveIsRefused(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-H-CAN', 'statut' => 1));
        $r = $this->api('POST', '/holidays/'.$id.'/cancel', self::KEY_MANAGER);
        $this->assertBlocked($r, 'cancelling an outside leave');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame('1', (string) $row['statut']);
    }

    public function testRefuseOutsideLeaveIsRefused(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-H-REF', 'statut' => 1));
        $r = $this->api('POST', '/holidays/'.$id.'/refuse', self::KEY_MANAGER, array('detail_refuse' => 'cwe-refuse'));
        $this->assertBlocked($r, 'refusing an outside leave');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame('1', (string) $row['statut']);
        $this->assertNull($row['detail_refuse']);
    }

    public function testReopenOutsideLeaveIsRefused(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-H-REO', 'statut' => 4));
        $r = $this->api('POST', '/holidays/'.$id.'/reopen', self::KEY_MANAGER);
        $this->assertBlocked($r, 'reopening an outside leave');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame('4', (string) $row['statut']);
    }
}
