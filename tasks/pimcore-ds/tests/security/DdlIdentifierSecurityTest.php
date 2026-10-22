<?php
declare(strict_types=1);

/*
 * Hidden security tests: identifiers and SQL fragments carried by a class
 * definition must not change the structure of the statements the definition
 * save executes. The tests drive the real Dao classes (including the shared DDL
 * implementation and the objectbrick-specific one) against a recording
 * connection, and assert that the attacker value is not visible outside a
 * quoted identifier or string literal.
 */

namespace Pimcore\Tests\Cwe\Security;

use PHPUnit\Framework\TestCase;
use Pimcore\Tests\Cwe\ClassDefinitionDaoProbe;
use Pimcore\Tests\Cwe\ObjectbrickDaoProbe;
use Pimcore\Model\DataObject\ClassDefinition\Data\StructuredTable;

use function Pimcore\Tests\Cwe\class_definition_from_layout;
use function Pimcore\Tests\Cwe\field_node;
use function Pimcore\Tests\Cwe\queries_contain_bare_marker;

final class DdlIdentifierSecurityTest extends TestCase
{
    private function dao(): ClassDefinitionDaoProbe
    {
        return new ClassDefinitionDaoProbe();
    }

    private function structuredTable(string $rowKey, string $columnKey, bool $indexed): StructuredTable
    {
        $class = class_definition_from_layout([
            field_node('structuredTable', [
                'name' => 'tbl',
                'title' => 'table',
                'rows' => [['key' => $rowKey, 'type' => 'text']],
                'cols' => [['key' => $columnKey, 'type' => 'text']],
                'index' => $indexed,
            ]),
        ]);

        $field = $class->getFieldDefinitions()['tbl'] ?? null;
        $this->assertInstanceOf(StructuredTable::class, $field);

        return $field;
    }


    /**
     * Runs one definition-save DDL step. A refusal (client error) counts as blocked;
     * otherwise the recorded statements must keep the marker inside a quoted value.
     *
     * @param callable(): void $operation
     */
    private function assertDdlBlocked(callable $operation, ClassDefinitionDaoProbe|ObjectbrickDaoProbe $dao, string $marker, string $message): void
    {
        try {
            $operation();
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);

            return;
        }

        $queries = $dao->recordedQueries();
        $this->assertNotEmpty($queries, 'the DDL path emitted no statement');
        $this->assertFalse(queries_contain_bare_marker($queries, $marker), $message);
    }

    public function testColumnLabelCannotBreakOutOfAddColumn(): void
    {
        $field = $this->structuredTable('r1', 'c`, PWN_DDL int); --', false);
        $dao = $this->dao();

        $this->assertDdlBlocked(
            function () use ($dao, $field): void {
                foreach ($field->getColumnType() as $columnName => $columnType) {
                    $dao->addColumnStatement('object_store_1', $field->getName() . '__' . $columnName, $columnType);
                }
            },
            $dao,
            'PWN_DDL',
            'a structured table label changed the structure of the ADD COLUMN statement'
        );
    }

    public function testRowLabelCannotBreakOutOfAddIndex(): void
    {
        $field = $this->structuredTable('r1`, PWN_IDX int); --', 'c1', true);
        $dao = $this->dao();

        $this->assertDdlBlocked(
            fn () => $dao->addIndexStatement($field, 'object_store_1', 'getColumnType'),
            $dao,
            'PWN_IDX',
            'a structured table label changed the structure of the ADD INDEX statement'
        );
    }

    public function testRowLabelCannotBreakOutOfDropIndex(): void
    {
        $field = $this->structuredTable('r1`, PWN_DROP int); --', 'c1', false);
        $dao = $this->dao();

        $indexName = 'p_index_' . $field->getName() . '__' . $field->getRows()[0]['key'] . '#' . $field->getCols()[0]['key'];
        $dao->connection()->existingIndexes['object_store_1'][$indexName] = true;

        $this->assertDdlBlocked(
            fn () => $dao->addIndexStatement($field, 'object_store_1', 'getColumnType'),
            $dao,
            'PWN_DROP',
            'a structured table label changed the structure of the DROP INDEX statement'
        );
    }

    public function testExistingColumnNameCannotBreakOutOfChangeColumn(): void
    {
        $payload = 'x`, PWN_CHG int); --';
        $dao = $this->dao();
        $dao->columns['object_store_1'] = [$payload];

        $this->assertDdlBlocked(
            fn () => $dao->addColumnStatement('object_store_1', $payload, 'bigint(20)'),
            $dao,
            'PWN_CHG',
            'a column name read back from the database changed the structure of the CHANGE COLUMN statement'
        );
    }

    public function testDatabaseColumnNameCannotBreakOutOfDropColumn(): void
    {
        $payload = 'x`, PWN_DBC int); --';
        $dao = $this->dao();
        $dao->columns['object_store_1'] = ['kept', $payload];
        // An index for the obsolete column exists too, so the same database-supplied
        // name reaches the index-drop statement as well as the column-drop statement.
        $dao->connection()->existingIndexes['object_store_1']['u_index_' . $payload] = true;

        $this->assertDdlBlocked(
            fn () => $dao->dropUnusedColumns('object_store_1', [$payload], ['kept']),
            $dao,
            'PWN_DBC',
            'a column name read back from the database changed the structure of a DROP statement'
        );

        $queries = $dao->recordedQueries();
        $this->assertTrue(
            array_filter($queries, static fn (string $q): bool => str_contains($q, 'DROP INDEX')) !== [],
            'the index-drop path emitted no statement'
        );
    }

    public function testObjectbrickDropIndexCannotBreakOut(): void
    {
        $payload = 'x`, PWN_OBJ int); --';
        $dao = new ObjectbrickDaoProbe();

        $this->assertDdlBlocked(
            fn () => $dao->dropIndexStatements('object_brick_store_1', [$payload], []),
            $dao,
            'PWN_OBJ',
            'a column name used by the objectbrick index drop changed the statement structure'
        );
    }

    public function testDefaultClauseCannotAddColumns(): void
    {
        $payload = ' DEFAULT 0, PWN_DEF int';

        try {
            $class = class_definition_from_layout([
                field_node('input', [
                    'name' => 'goodField',
                    'title' => 'field',
                    'defaultValueSql' => $payload,
                ]),
            ]);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);

            return;
        }

        $field = $class->getFieldDefinitions()['goodField'];
        $default = method_exists($field, 'getDefaultValueSql') ? (string) $field->getDefaultValueSql() : '';

        $dao = $this->dao();
        $this->assertDdlBlocked(
            fn () => $dao->addColumnStatement('object_store_1', 'goodField', 'varchar(190)', $default),
            $dao,
            'PWN_DEF',
            'a definition supplied default clause changed the structure of the ADD COLUMN statement'
        );
    }

    public function testTooltipCannotBreakOutOfTheColumnComment(): void
    {
        $payload = "help', PWN_COMMENT int); --";

        try {
            $class = class_definition_from_layout([
                field_node('input', ['name' => 'goodField', 'title' => 'field', 'tooltip' => $payload]),
            ]);
            $field = $class->getFieldDefinitions()['goodField'];
            $comment = (string) ($field->getTooltip() ?? '');
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);

            return;
        }

        $dao = $this->dao();
        $this->assertDdlBlocked(
            fn () => $dao->addColumnStatement('object_store_1', 'goodField', 'varchar(190)', '', 'NULL', $comment),
            $dao,
            'PWN_COMMENT',
            'a definition supplied help text ended the column comment and changed the statement structure'
        );
    }

    public function testColumnTypeCannotBreakOutOfTheColumnDefinition(): void
    {
        $payload = 'bigint(20), PWN_TYPE int); --';

        try {
            $class = class_definition_from_layout([
                field_node('date', ['name' => 'd', 'title' => 'date', 'columnType' => $payload]),
            ]);
            $field = $class->getFieldDefinitions()['d'];
            $type = (string) $field->getColumnType();
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);

            return;
        }

        $dao = $this->dao();
        $this->assertDdlBlocked(
            fn () => $dao->addColumnStatement('object_store_1', $field->getName(), $type),
            $dao,
            'PWN_TYPE',
            'a definition supplied column type changed the structure of the ADD COLUMN statement'
        );
    }

    public function testEveryRangeColumnTypeCannotBreakOutOfTheColumnDefinition(): void
    {
        $payload = 'bigint(20), PWN_RANGE int); --';

        try {
            $class = class_definition_from_layout([
                field_node('dateRange', [
                    'name' => 'r',
                    'title' => 'range',
                    'columnType' => ['start_date' => $payload, 'end_date' => $payload],
                ]),
            ]);
            $field = $class->getFieldDefinitions()['r'];
            $types = $field->getColumnType();
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);

            return;
        }

        $this->assertIsArray($types);
        $dao = $this->dao();
        $this->assertDdlBlocked(
            function () use ($dao, $field, $types): void {
                foreach ($types as $columnName => $columnType) {
                    $dao->addColumnStatement('object_store_1', $field->getName() . '__' . $columnName, (string) $columnType);
                }
            },
            $dao,
            'PWN_RANGE',
            'a definition supplied range column type changed the structure of the ADD COLUMN statement'
        );
    }
}
