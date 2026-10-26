<?php
/**
 * A derived view of a leave request is information about that record and must apply the
 * same management-hierarchy rule as the record itself.
 */
class LeaveSummarySecurityTest extends ApiTestCase
{
    public function testSummaryOfOutsideLeaveIsRefusedForAManager(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-SUM-M', 'description' => 'cwe summary marker'));
        $r = $this->api('GET', '/holidays/'.$id.'/summary', self::KEY_MANAGER);
        $this->assertBlocked($r, 'reading a summary of an outside leave');
        $this->assertBodyLacks($r, 'CWETEST-SUM-M');
        $this->assertBodyLacks($r, 'cwe summary marker');
    }

    public function testSummaryOfOutsideLeaveIsRefusedForAnUnrelatedEmployee(): void
    {
        $id = $this->mkLeave(array('ref' => 'CWETEST-SUM-S', 'description' => 'cwe summary marker two'));
        $r = $this->api('GET', '/holidays/'.$id.'/summary', self::KEY_SUB);
        $this->assertBlocked($r, 'reading a summary of an outside leave as an unrelated employee');
        $this->assertBodyLacks($r, 'CWETEST-SUM-S');
    }
}
