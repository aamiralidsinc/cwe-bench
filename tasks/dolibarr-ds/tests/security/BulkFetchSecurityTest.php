<?php
/**
 * A request that asks for several leave requests at once must still apply the
 * management-hierarchy rule to every record it returns.
 */
class BulkFetchSecurityTest extends ApiTestCase
{
    public function testBatchReadDoesNotDiscloseAnOutsideLeave(): void
    {
        $outside = $this->mkLeave(array('ref' => 'CWETEST-BLK-OUT', 'description' => 'cwe batch outside'));
        $inside = $this->mkLeave(array('ref' => 'CWETEST-BLK-IN', 'fk_user' => self::UID_SUB, 'fk_validator' => self::UID_MANAGER));

        $r = $this->api('GET', '/holidays/bulk?ids='.$inside.','.$outside, self::KEY_MANAGER);
        $this->assertNotDisclosed($r, 'CWETEST-BLK-OUT', 'batch read mixing an inside and an outside leave');
        $this->assertNotDisclosed($r, 'cwe batch outside', 'content of an outside leave');
    }

    public function testSingleRecordBatchReadDoesNotDiscloseAnOutsideLeave(): void
    {
        $outside = $this->mkLeave(array('ref' => 'CWETEST-BLK-ONE', 'description' => 'cwe batch single outside'));

        $r = $this->api('GET', '/holidays/bulk?ids='.$outside, self::KEY_MANAGER);
        $this->assertNotDisclosed($r, 'CWETEST-BLK-ONE', 'batch read of an outside leave');
    }
}
