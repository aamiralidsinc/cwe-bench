<?php
/**
 * Legitimate expense-report use must keep working for managers acting on their reports'
 * records and for holders of the broader all-user permission.
 */
class ExpenseLegitTest extends ApiTestCase
{
    protected function lineBody(array $over = array()): array
    {
        return array_merge(array(
            'fk_c_type_fees' => 2,
            'comments' => 'cwe-line',
            'qty' => 1,
            'value_unit' => 10,
            'vatrate' => 0,
            'date' => date('Y-m-d', strtotime('-10 days')),
            'fk_project' => 0,
            'fk_c_exp_tax_cat' => 0,
            'type' => 0,
            'fk_ecm_files' => 0,
        ), $over);
    }

    protected function subReport(array $over = array()): int
    {
        return $this->mkExpense(array_merge(array(
            'fk_user_author' => self::UID_SUB,
            'fk_user_creat' => self::UID_SUB,
        ), $over));
    }

    public function testManagerReadsSubordinateReport(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-GET'));
        $r = $this->api('GET', '/expensereports/'.$id, self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager reading a subordinate report');
        $this->assertBodyHas($r, 'CWETEST-FE-GET');
    }

    public function testManagerReadsSubordinateReportLines(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-LIN'));
        $this->mkLine($id, array('comments' => 'cwe legit line'));
        $r = $this->api('GET', '/expensereports/'.$id.'/lines', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager reading a subordinate report lines');
        $this->assertBodyHas($r, 'cwe legit line');
    }

    public function testManagerAddsLine(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-ADD', 'fk_statut' => 0));
        $before = $this->countRows('SELECT COUNT(*) FROM llx_expensereport_det WHERE fk_expensereport = '.((int) $id));
        $r = $this->api('POST', '/expensereports/'.$id.'/line', self::KEY_MANAGER, $this->lineBody(array('comments' => 'cwe added line')));
        $this->assertAllowed($r, 'manager adding a line');
        $after = $this->countRows('SELECT COUNT(*) FROM llx_expensereport_det WHERE fk_expensereport = '.((int) $id));
        $this->assertSame($before + 1, $after);
    }

    public function testManagerUpdatesLine(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-UPL', 'fk_statut' => 0));
        $line = $this->mkLine($id, array('comments' => 'old'));
        $r = $this->api('PUT', '/expensereports/'.$id.'/lines/'.$line, self::KEY_MANAGER, $this->lineBody(array('comments' => 'cwe updated line')));
        $this->assertAllowed($r, 'manager updating a line');
        $this->assertSame('cwe updated line', $this->row('llx_expensereport_det', $line)['comments']);
    }

    public function testManagerDeletesLine(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-DLL', 'fk_statut' => 0));
        $line = $this->mkLine($id);
        $r = $this->api('DELETE', '/expensereports/'.$id.'/lines/'.$line, self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager deleting a line');
        $this->assertNull($this->row('llx_expensereport_det', $line));
    }

    public function testManagerUpdatesReport(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-PUT', 'note_public' => 'old'));
        $r = $this->api('PUT', '/expensereports/'.$id, self::KEY_MANAGER, array('note_public' => 'cwe manager note'));
        $this->assertAllowed($r, 'manager updating a report');
        $this->assertSame('cwe manager note', $this->row('llx_expensereport', $id)['note_public']);
    }

    public function testManagerSetsReportToDraft(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-DRF', 'fk_statut' => 2));
        $r = $this->api('POST', '/expensereports/'.$id.'/settodraft', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager setting a report to draft');
        $this->assertSame('0', (string) $this->row('llx_expensereport', $id)['fk_statut']);
    }

    public function testManagerValidatesReport(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-VAL', 'fk_statut' => 0));
        $r = $this->api('POST', '/expensereports/'.$id.'/validate', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager validating a report');
        $this->assertSame('2', (string) $this->row('llx_expensereport', $id)['fk_statut']);
    }

    public function testManagerApprovesReport(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-APP', 'fk_statut' => 2));
        $r = $this->api('POST', '/expensereports/'.$id.'/approve', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager approving a report');
        $this->assertSame('5', (string) $this->row('llx_expensereport', $id)['fk_statut']);
    }

    public function testManagerDeniesReport(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-DNY', 'fk_statut' => 0));
        $r = $this->api('POST', '/expensereports/'.$id.'/deny', self::KEY_MANAGER, array('details' => 'cwe denied'));
        $this->assertAllowed($r, 'manager denying a report');
        $this->assertSame('99', (string) $this->row('llx_expensereport', $id)['fk_statut']);
    }

    public function testManagerPaysReport(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-PAY', 'fk_statut' => 5));
        $r = $this->api('POST', '/expensereports/'.$id.'/setpaid', self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager paying a report');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame('6', (string) $row['fk_statut']);
        $this->assertSame('1', (string) $row['paid']);
    }

    public function testManagerCancelsReport(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-CAN', 'fk_statut' => 0));
        $r = $this->api('POST', '/expensereports/'.$id.'/cancel', self::KEY_MANAGER, array('detail' => 'cwe cancelled'));
        $this->assertAllowed($r, 'manager cancelling a report');
        $this->assertSame('4', (string) $this->row('llx_expensereport', $id)['fk_statut']);
    }

    public function testManagerDeletesReport(): void
    {
        $id = $this->subReport(array('ref' => 'CWETEST-FE-DEL', 'fk_statut' => 0));
        $r = $this->api('DELETE', '/expensereports/'.$id, self::KEY_MANAGER);
        $this->assertAllowed($r, 'manager deleting a report');
        $this->assertNull($this->row('llx_expensereport', $id));
    }

    public function testAllUserPermissionReadsOutsideReport(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-FE-ALL', 'fk_user_author' => self::UID_OUT));
        $r = $this->api('GET', '/expensereports/'.$id, self::KEY_ALL);
        $this->assertAllowed($r, 'all-user permission reading a report');
        $this->assertBodyHas($r, 'CWETEST-FE-ALL');
    }
}
