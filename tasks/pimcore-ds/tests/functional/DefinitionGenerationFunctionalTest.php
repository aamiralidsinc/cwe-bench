<?php
declare(strict_types=1);

/*
 * Functional tests: ordinary class definitions keep generating the same model
 * classes, and the coupled behaviour next to every protected sink keeps working
 * (valid names and boundaries, the fixed localized-fields name, an empty name set
 * transiently, classification store fields, titles and legacy accessors).
 */

namespace Pimcore\Tests\Cwe\Functional;

use PHPUnit\Framework\TestCase;
use Pimcore\Model\DataObject\ClassDefinition\Data\Input;
use Pimcore\Model\DataObject\ClassDefinition\Data\Localizedfields;

use function Pimcore\Tests\Cwe\build_class_code;
use function Pimcore\Tests\Cwe\class_definition_from_layout;
use function Pimcore\Tests\Cwe\clear_generated_files;
use function Pimcore\Tests\Cwe\dump_class_files;
use function Pimcore\Tests\Cwe\field_node;
use function Pimcore\Tests\Cwe\string_literal_values;

final class DefinitionGenerationFunctionalTest extends TestCase
{
    private const CLASS_NAME = 'TaskClass';

    protected function setUp(): void
    {
        clear_generated_files();
    }

    protected function tearDown(): void
    {
        clear_generated_files();
    }

    public function testValidDefinitionGeneratesConstantsAccessorsAndTitle(): void
    {
        $class = class_definition_from_layout(
            [field_node('input', ['name' => 'goodField', 'title' => 'A good field'])],
            self::CLASS_NAME
        );

        $code = build_class_code($class);

        $this->assertStringContainsString("public const FIELD_GOOD_FIELD = 'goodField';", $code);
        $this->assertStringContainsString('public function getGoodField(', $code);
        $this->assertStringContainsString('public function setGoodField(', $code);
        $this->assertStringContainsString('A good field', $code);
    }

    public function testValidNameBoundariesAreAccepted(): void
    {
        foreach (['a', '_internal', 'field_123', str_repeat('a', 63)] as $name) {
            $class = class_definition_from_layout(
                [field_node('input', ['name' => $name, 'title' => 'field'])],
                self::CLASS_NAME
            );
            $code = build_class_code($class);
            $this->assertStringContainsString('get' . ucfirst($name) . '(', $code, 'name ' . $name . ' must still generate');
        }
    }

    public function testEmptyNameIsAcceptedTransiently(): void
    {
        $field = new Input();
        $field->setName('');

        $this->assertSame('', $field->getName());
    }

    public function testLocalizedFieldsKeepsItsFixedName(): void
    {
        $field = new Localizedfields();
        $field->setName('localizedfields');

        $this->assertSame('localizedfields', $field->getName());
    }

    /**
     * The project's own expectation for the generated setter code of a plain input
     * field (tests/Model/DataObject/ClassDefinitionTest::testInputSetterCode).
     */
    public function testGeneratedSetterCodeForInputFieldIsUnchanged(): void
    {
        $class = class_definition_from_layout(
            [field_node('input', ['name' => 'input', 'title' => 'input'])],
            self::CLASS_NAME
        );

        $field = $class->getFieldDefinitions()['input'];
        $expected = '/**
* Set input - input
* @param string|null $input
* @return $this
*/
public function setInput(?string $input): static
{
	$this->markFieldDirty("input", true);

	$this->input = $input;

	return $this;
}

';

        $this->assertSame($expected, $field->getSetterCode($class));
    }

    public function testClassificationStoreFieldStillGeneratesAccessors(): void
    {
        $class = class_definition_from_layout(
            [field_node('classificationstore', ['name' => 'categories', 'title' => 'Categories'])],
            self::CLASS_NAME
        );

        $code = build_class_code($class);

        $this->assertStringContainsString('public function getCategories(', $code);
        $this->assertStringContainsString('public function setCategories(', $code);
    }

    public function testLegacyAccessorAliasStillGeneratesItsMethod(): void
    {
        $class = class_definition_from_layout(
            [field_node('input', ['name' => 'goodField', 'title' => 'field', 'legacyName' => 'oldField'])],
            self::CLASS_NAME
        );

        $code = build_class_code($class);

        $this->assertStringContainsString('public function getOldField()', $code);
        $this->assertStringContainsString('return $this->getGoodField();', $code);
    }

    public function testDumpWritesTheClassFileForAValidDefinition(): void
    {
        $class = class_definition_from_layout(
            [field_node('input', ['name' => 'goodField', 'title' => 'field'])],
            self::CLASS_NAME
        );

        $path = dump_class_files($class, self::CLASS_NAME);

        $this->assertFileExists($path);
        $this->assertStringContainsString('class ' . self::CLASS_NAME, (string) file_get_contents($path));
    }

    public function testOrdinaryTitleIsKeptAsDataInTheGeneratedClass(): void
    {
        $class = class_definition_from_layout(
            [field_node('input', ['name' => 'goodField', 'title' => 'A good field'])],
            self::CLASS_NAME
        );

        $literals = string_literal_values(build_class_code($class));

        $this->assertContains('goodField', $literals, 'the field key is kept as data in the generated class');
        $this->assertContains('A good field', $literals, 'the display title is kept as data in the generated class');
    }
}
