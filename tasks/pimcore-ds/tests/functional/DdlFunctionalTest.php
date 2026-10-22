<?php
declare(strict_types=1);

/*
 * Functional tests for the database side: ordinary definitions keep producing the
 * same column and index statements, including the coupled shapes (structured table
 * labels, multi-column date ranges, unique localized indexes, defaults, renames
 * and the objectbrick index drop).
 */

namespace Pimcore\Tests\Cwe\Functional;

use PHPUnit\Framework\TestCase;
use Pimcore\Tests\Cwe\ClassDefinitionDaoProbe;
use Pimcore\Tests\Cwe\ObjectbrickDaoProbe;
use Pimcore\Model\DataObject\ClassDefinition\Data\Input;
use Pimcore\Model\DataObject\ClassDefinition\Data\StructuredTable;

use function Pimcore\Tests\Cwe\class_definition_from_layout;
use function Pimcore\Tests\Cwe\field_node;

final class DdlFunctionalTest extends TestCase
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
        $field = $class->getFieldDefinitions()['tbl'];
        $this->assertInstanceOf(StructuredTable::class, $field);

        return $field;
    }

    public function testStructuredTableColumnsKeepTheirNames(): void
    {
        $field = $this->structuredTable('row 1', 'col-2', false);
        $dao = $this->dao();

        foreach ($field->getColumnType() as $columnName => $columnType) {
            $dao->addColumnStatement('object_store_1', $field->getName() . '__' . $columnName, $columnType);
        }

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('tbl__row 1#col-2', $queries);
        $this->assertStringContainsString('ADD COLUMN', $queries);
    }

    public function testStructuredTableIndexIsCreatedAndDropped(): void
    {
        $indexed = $this->structuredTable('row 1', 'col-2', true);
        $dao = $this->dao();
        $dao->addIndexStatement($indexed, 'object_store_1', 'getColumnType');

        $added = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('ADD INDEX', $added);
        $this->assertStringContainsString('p_index_tbl__row 1#col-2', $added);

        $unindexed = $this->structuredTable('row 1', 'col-2', false);
        $dropDao = $this->dao();
        $dropDao->connection()->existingIndexes['object_store_1']['p_index_tbl__row 1#col-2'] = true;
        $dropDao->addIndexStatement($unindexed, 'object_store_1', 'getColumnType');

        $dropped = implode("\n", $dropDao->recordedQueries());
        $this->assertStringContainsString('DROP INDEX', $dropped);
        $this->assertStringContainsString('p_index_tbl__row 1#col-2', $dropped);
    }

    public function testFieldColumnTypesAreAccepted(): void
    {
        $class = class_definition_from_layout([
            field_node('input', ['name' => 'plainInput', 'title' => 'input']),
            field_node('date', ['name' => 'plainDate', 'title' => 'date']),
            field_node('dateRange', ['name' => 'range', 'title' => 'range']),
        ]);

        $dao = $this->dao();
        foreach ($class->getFieldDefinitions() as $field) {
            $types = $field->getColumnType();
            if (!is_array($types)) {
                $types = [$field->getName() => $types];
            }
            foreach ($types as $key => $type) {
                $columnName = $key === $field->getName() ? $field->getName() : $field->getName() . '__' . $key;
                $dao->addColumnStatement('object_store_1', $columnName, (string) $type);
            }
        }

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('varchar(190)', $queries);
        $this->assertStringContainsString('bigint(20)', $queries);
        $this->assertStringContainsString('start_date', $queries);
        $this->assertStringContainsString('end_date', $queries);
    }

    public function testValidDefaultClauseIsApplied(): void
    {
        $class = class_definition_from_layout([
            field_node('input', ['name' => 'goodField', 'title' => 'field', 'defaultValueSql' => ' DEFAULT 0']),
        ]);
        $field = $class->getFieldDefinitions()['goodField'];
        $default = method_exists($field, 'getDefaultValueSql') ? (string) $field->getDefaultValueSql() : '';

        $dao = $this->dao();
        $dao->addColumnStatement('object_store_1', 'goodField', 'varchar(190)', $default);

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('DEFAULT 0', $queries);
    }

    public function testExistingColumnIsRenamedCaseInsensitively(): void
    {
        $dao = $this->dao();
        $dao->columns['object_store_1'] = ['legacyField'];
        $dao->addColumnStatement('object_store_1', 'legacyfield', 'bigint(20)');

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('CHANGE COLUMN', $queries);
        $this->assertStringContainsString('legacyField', $queries);
        $this->assertStringContainsString('legacyfield', $queries);
    }

    public function testUnusedColumnIsDropped(): void
    {
        $dao = $this->dao();
        $dao->columns['object_store_1'] = ['keptColumn', 'obsoleteColumn'];

        $dao->dropUnusedColumns('object_store_1', ['keptColumn', 'obsoleteColumn'], ['keptColumn']);

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('DROP COLUMN', $queries);
        $this->assertStringContainsString('obsoleteColumn', $queries);
        $this->assertStringNotContainsString('keptColumn', $queries);
    }

    public function testObjectbrickIndexDropStillEmitsItsStatement(): void
    {
        $dao = new ObjectbrickDaoProbe();
        $dao->dropIndexStatements('object_brick_store_1', ['obsoleteColumn'], []);

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('DROP INDEX', $queries);
        $this->assertStringContainsString('u_index_obsoleteColumn', $queries);
    }

    public function testUniqueLocalizedIndexKeepsTheLanguageColumn(): void
    {
        $class = class_definition_from_layout([
            field_node('input', ['name' => 'code', 'title' => 'code', 'unique' => true]),
        ]);
        $field = $class->getFieldDefinitions()['code'];
        $this->assertInstanceOf(Input::class, $field);

        $dao = $this->dao();
        $dao->addIndexStatement($field, 'object_localized_1', 'getColumnType', true, true);

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('UNIQUE INDEX', $queries);
        $this->assertStringContainsString('code', $queries);
        $this->assertStringContainsString('language', $queries);
    }

    public function testIndexedInputCreatesItsSingleColumnIndex(): void
    {
        $class = class_definition_from_layout([
            field_node('input', ['name' => 'code', 'title' => 'code', 'index' => true]),
        ]);
        $field = $class->getFieldDefinitions()['code'];

        $dao = $this->dao();
        $dao->addIndexStatement($field, 'object_store_1', 'getColumnType');

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString('ADD INDEX', $queries);
        $this->assertStringContainsString('p_index_code', $queries);
    }

    public function testOrdinaryTooltipIsWrittenAsTheColumnComment(): void
    {
        $class = class_definition_from_layout([
            field_node('input', ['name' => 'goodField', 'title' => 'field', 'tooltip' => 'Some help']),
        ]);
        $field = $class->getFieldDefinitions()['goodField'];

        $dao = $this->dao();
        $dao->addColumnStatement('object_store_1', 'goodField', 'varchar(190)', '', 'NULL', (string) ($field->getTooltip() ?? ''));

        $queries = implode("\n", $dao->recordedQueries());
        $this->assertStringContainsString("COMMENT 'Some help'", $queries);
    }

    public function testConfigurableColumnTypesAreApplied(): void
    {
        $class = class_definition_from_layout([
            field_node('date', ['name' => 'd', 'title' => 'date', 'columnType' => 'int(11)']),
        ]);
        $field = $class->getFieldDefinitions()['d'];

        $dao = $this->dao();
        $dao->addColumnStatement('object_store_1', $field->getName(), (string) $field->getColumnType());
        $this->assertStringContainsString('int(11)', implode("\n", $dao->recordedQueries()));

        $class = class_definition_from_layout([
            field_node('dateRange', [
                'name' => 'r',
                'title' => 'range',
                'columnType' => ['start_date' => 'int(11)', 'end_date' => 'bigint(20)'],
            ]),
        ]);
        $field = $class->getFieldDefinitions()['r'];
        $types = $field->getColumnType();
        $this->assertIsArray($types);

        $rangeDao = $this->dao();
        foreach ($types as $columnName => $columnType) {
            $rangeDao->addColumnStatement('object_store_1', $field->getName() . '__' . $columnName, (string) $columnType);
        }
        $rangeQueries = implode("\n", $rangeDao->recordedQueries());
        $this->assertStringContainsString('r__start_date', $rangeQueries);
        $this->assertStringContainsString('r__end_date', $rangeQueries);
        $this->assertStringContainsString('int(11)', $rangeQueries);
        $this->assertStringContainsString('bigint(20)', $rangeQueries);
    }
}
