<?php
/**
 * Per-record expense-report endpoints (and their lines) must apply the same
 * management-hierarchy rule. The caller is the manager of user 3; every record below
 * belongs to user 4, who is outside that manager's hierarchy.
 */
class ExpenseObjectAccessTest extends ApiTestCase
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

    public function testGetOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-GET', 'note_public' => 'cwe report marker'));
        $r = $this->api('GET', '/expensereports/'.$id, self::KEY_MANAGER);
        $this->assertBlocked($r, 'reading an outside report');
        $this->assertBodyLacks($r, 'cwe report marker');
    }

    public function testGetOutsideReportLinesIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-LIN'));
        $line = $this->mkLine($id, array('comments' => 'cwe line marker'));
        $r = $this->api('GET', '/expensereports/'.$id.'/lines', self::KEY_MANAGER);
        $this->assertBlocked($r, 'reading the lines of an outside report');
        $this->assertBodyLacks($r, 'cwe line marker');
        $this->assertNotNull($this->row('llx_expensereport_det', $line));
    }

    public function testAddLineToOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-ADD', 'fk_statut' => 0));
        $before = $this->countRows('SELECT COUNT(*) FROM llx_expensereport_det WHERE fk_expensereport = '.((int) $id));
        $r = $this->api('POST', '/expensereports/'.$id.'/line', self::KEY_MANAGER, $this->lineBody(array('comments' => 'cwe-injected-line')));
        $this->assertBlocked($r, 'adding a line to an outside report');
        $after = $this->countRows('SELECT COUNT(*) FROM llx_expensereport_det WHERE fk_expensereport = '.((int) $id));
        $this->assertSame($before, $after);
    }

    public function testUpdateOutsideReportLineIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-UPL', 'fk_statut' => 0));
        $line = $this->mkLine($id, array('comments' => 'unchanged'));
        $r = $this->api('PUT', '/expensereports/'.$id.'/lines/'.$line, self::KEY_MANAGER, $this->lineBody(array('comments' => 'cwe-updated-line')));
        $this->assertBlocked($r, 'updating a line of an outside report');
        $row = $this->row('llx_expensereport_det', $line);
        $this->assertSame('unchanged', $row['comments']);
    }

    public function testDeleteOutsideReportLineIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-DLL', 'fk_statut' => 0));
        $line = $this->mkLine($id);
        $r = $this->api('DELETE', '/expensereports/'.$id.'/lines/'.$line, self::KEY_MANAGER);
        $this->assertBlocked($r, 'deleting a line of an outside report');
        $this->assertNotNull($this->row('llx_expensereport_det', $line));
    }

    public function testUpdateOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-PUT', 'note_public' => 'unchanged'));
        $r = $this->api('PUT', '/expensereports/'.$id, self::KEY_MANAGER, array('note_public' => 'cwe-updated-report'));
        $this->assertBlocked($r, 'updating an outside report');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame('unchanged', $row['note_public']);
    }

    public function testDeleteOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-DEL'));
        $r = $this->api('DELETE', '/expensereports/'.$id, self::KEY_MANAGER);
        $this->assertBlocked($r, 'deleting an outside report');
        $this->assertNotNull($this->row('llx_expensereport', $id));
    }

    public function testSetOutsideReportToDraftIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-DRF', 'fk_statut' => 2));
        $r = $this->api('POST', '/expensereports/'.$id.'/settodraft', self::KEY_MANAGER);
        $this->assertBlocked($r, 'setting an outside report back to draft');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame('2', (string) $row['fk_statut']);
    }

    public function testValidateOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-VAL', 'fk_statut' => 0));
        $r = $this->api('POST', '/expensereports/'.$id.'/validate', self::KEY_MANAGER);
        $this->assertBlocked($r, 'validating an outside report');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame('0', (string) $row['fk_statut']);
    }

    public function testApproveOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-APP', 'fk_statut' => 2));
        $r = $this->api('POST', '/expensereports/'.$id.'/approve', self::KEY_MANAGER);
        $this->assertBlocked($r, 'approving an outside report');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame('2', (string) $row['fk_statut']);
    }

    public function testDenyOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-DNY', 'fk_statut' => 0));
        $r = $this->api('POST', '/expensereports/'.$id.'/deny', self::KEY_MANAGER, array('details' => 'cwe-deny'));
        $this->assertBlocked($r, 'denying an outside report');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame('0', (string) $row['fk_statut']);
        $this->assertNull($row['detail_refuse']);
    }

    public function testPayOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-PAY', 'fk_statut' => 5));
        $r = $this->api('POST', '/expensereports/'.$id.'/setpaid', self::KEY_MANAGER);
        $this->assertBlocked($r, 'paying an outside report');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame('5', (string) $row['fk_statut']);
        $this->assertSame('0', (string) $row['paid']);
    }

    public function testCancelOutsideReportIsRefused(): void
    {
        $id = $this->mkExpense(array('ref' => 'CWETEST-E-CAN', 'fk_statut' => 0));
        $r = $this->api('POST', '/expensereports/'.$id.'/cancel', self::KEY_MANAGER, array('detail' => 'cwe-cancel'));
        $this->assertBlocked($r, 'cancelling an outside report');
        $row = $this->row('llx_expensereport', $id);
        $this->assertSame('0', (string) $row['fk_statut']);
    }
}
