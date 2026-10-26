<?php
/**
 * Legitimate leave-request use must keep working: self-service, managers acting for their
 * reports, designated approvers, and holders of the broader all-user permission.
 */
class HolidayLegitTest extends ApiTestCase
{
    public function testManagerReadsSubordinateLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-MGR', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('GET', '/holidays/'.$id, self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager reading a subordinate leave');
        $this->assertBodyHas($r, 'CWETEST-F-MGR');
    }

    public function testEmployeeReadsOwnLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-OWN', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('GET', '/holidays/'.$id, self::KEY_SUB);
        $this->assertAllowed($r, 'employee reading own leave');
        $this->assertBodyHas($r, 'CWETEST-F-OWN');
    }

    public function testDesignatedApproverReadsLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-APR', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_VAL));
        $r = $this->api('GET', '/holidays/'.$id, self::KEY_VAL);
        $this->assertAllowed($r, 'designated approver reading a leave');
        $this->assertBodyHas($r, 'CWETEST-F-APR');
    }

    public function testAllUserPermissionReadsLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-ALL', 'fk_user' => self::UID_OUT));
        $r = $this->api('GET', '/holidays/'.$id, self::KEY_ALL);
        $this->assertAllowed($r, 'all-user permission reading a leave');
        $this->assertBodyHas($r, 'CWETEST-F-ALL');
    }

    public function testManagerUpdatesSubordinateLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-PUT', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('PUT', '/holidays/'.$id, self::KEY_MANAGER, array('description' => 'cwe-manager-update'));
        $this->assertAllowed($r, 'manager updating a subordinate leave');
        $row = $this->row('llx_holiday', $id);
        $this->assertSame('cwe-manager-update', $row['description']);
    }

    public function testManagerValidatesSubordinateLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-VAL', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER, 'statut' => 1));
        $r = $this->api('POST', '/holidays/'.$id.'/validate', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager validating a subordinate leave');
        $this->assertSame('2', (string) $this->row('llx_holiday', $id)['statut']);
    }

    public function testManagerApprovesSubordinateLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-APP', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER, 'statut' => 2));
        $r = $this->api('POST', '/holidays/'.$id.'/approve', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager approving a subordinate leave');
        $this->assertSame('3', (string) $this->row('llx_holiday', $id)['statut']);
    }

    public function testManagerCancelsSubordinateLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-CAN', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER, 'statut' => 2));
        $r = $this->api('POST', '/holidays/'.$id.'/cancel', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager cancelling a subordinate leave');
        $this->assertSame('4', (string) $this->row('llx_holiday', $id)['statut']);
    }

    public function testManagerRefusesSubordinateLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-REF', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER, 'statut' => 2));
        $r = $this->api('POST', '/holidays/'.$id.'/refuse', self::KEY_MANAGER, array('detail_refuse' => 'cwe-manager-refuse'));
        $this->assertAllowed($r, 'manager refusing a subordinate leave');
        $this->assertSame('5', (string) $this->row('llx_holiday', $id)['statut']);
    }

    public function testManagerReopensSubordinateLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-REO', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER, 'statut' => 4));
        $r = $this->api('POST', '/holidays/'.$id.'/reopen', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager reopening a subordinate leave');
        $this->assertSame('2', (string) $this->row('llx_holiday', $id)['statut']);
    }

    public function testManagerDeletesSubordinateLeave(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-DEL', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('DELETE', '/holidays/'.$id, self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager deleting a subordinate leave');
        $this->assertNull($this->row('llx_holiday', $id));
    }

    public function testManagerReadsSubordinateLeaveSummary(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-SUM', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('GET', '/holidays/'.$id.'/summary', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager reading a subordinate leave summary');
        $this->assertBodyHas($r, 'CWETEST-F-SUM');
    }

    public function testDesignatedApproverReadsLeaveSummary(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-F-SUMV', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_VAL));
        $r = $this->api('GET', '/holidays/'.$id.'/summary', self::KEY_VAL);
        $this->assertAllowed($r, 'designated approver reading a leave summary');
        $this->assertBodyHas($r, 'CWETEST-F-SUMV');
    }

    public function testBatchReadOfOwnAndSubordinateLeaves(): void
    {
        $own = $this->mkLeave(array('ref' => 'CWETEST-F-BLK1', 'fk_user' => self::UID_MANAGER, 'fk_validator' => self::UID_ADMIN));
        $sub = $this->mkLeave(array('ref' => 'CWETEST-F-BLK2', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));
        $r = $this->api('GET', '/holidays/bulk?ids='.$own.','.$sub, self::KEY_MANAGER);
        $this->assertAllowed($r, 'batch read of own and subordinate leaves');
        $this->assertBodyHas($r, 'CWETEST-F-BLK1');
        $this->assertBodyHas($r, 'CWETEST-F-BLK2');
    }
}
