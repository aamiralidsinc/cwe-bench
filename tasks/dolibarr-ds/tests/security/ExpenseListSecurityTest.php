<?php
/**
 * List results must not disclose expense reports of users outside the caller's hierarchy.
 */
class ExpenseListSecurityTest extends ApiTestCase
{
    public function testListDoesNotDiscloseAnOutsideReport(): void
    {
        $outside = $this->mkExpense(array('ref' => 'CWETEST-LST-OUT', 'fk_user_author' => self::UID_OUT, 'note_public' => 'cwe-list-outside'));
        $inside = $this->mkExpense(array('ref' => 'CWETEST-LST-IN', 'fk_user_author' => self::UID_SUB, 'note_public' => 'cwe-list-inside'));

        $r = $this->api('GET', '/expensereports', self::KEY_MANAGER);
        if ($r['status'] >= 400) {
            $this->assertBlocked($r, 'listing expense reports');
            return;
        }
        $this->assertSame(200, $r['status'], 'unexpected status: '.substr($r['body'], 0, 400));
        $this->assertBodyHas($r, 'CWETEST-LST-IN', 'the report of a subordinate');
        $this->assertBodyLacks($r, 'CWETEST-LST-OUT', 'the report of an outside user');
        $this->assertBodyLacks($r, 'cwe-list-outside', 'the content of an outside report');
    }

    public function testListFilterCannotSelectAnOutsideReport(): void
    {
        $outside = $this->mkExpense(array('ref' => 'CWETEST-LST-FLT', 'fk_user_author' => self::UID_OUT, 'note_public' => 'cwe-filter-outside'));

        $r = $this->api('GET', '/expensereports?user_ids='.self::UID_OUT, self::KEY_MANAGER);
        if ($r['status'] >= 400) {
            $this->assertBlocked($r, 'filtering expense reports by an outside user');
            return;
        }
        $this->assertSame(200, $r['status'], 'unexpected status: '.substr($r['body'], 0, 400));
        $this->assertBodyLacks($r, 'CWETEST-LST-FLT', 'the filtered report of an outside user');
    }
}
