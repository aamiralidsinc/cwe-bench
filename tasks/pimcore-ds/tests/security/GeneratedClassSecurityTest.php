<?php
declare(strict_types=1);

/*
 * Hidden security tests: values carried by a class definition must not become
 * executable code in the generated PHP class files. Each test drives the real
 * definition-application and class-generation path and asserts that the attacker
 * value neither runs nor survives as a token outside comments and strings.
 */

namespace Pimcore\Tests\Cwe\Security;

use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

use function Pimcore\Tests\Cwe\build_class_code;
use function Pimcore\Tests\Cwe\class_definition_from_layout;
use function Pimcore\Tests\Cwe\clear_generated_files;
use function Pimcore\Tests\Cwe\dump_class_files;
use function Pimcore\Tests\Cwe\field_node;
use function Pimcore\Tests\Cwe\has_executable_marker;

final class GeneratedClassSecurityTest extends TestCase
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

    /**
     * @return array<string, array{string}>
     */
    public static function invalidNameProvider(): array
    {
        return [
            'statement and comment' => ['x; echo PWN_NAME;//'],
            'braces and comment' => ['x{public function pwn(){}}//'],
            'backtick and semicolon' => ['x`; echo PWN_NAME;//'],
            'leading digit' => ['1field'],
            'space' => ['my field'],
            'dash' => ['my-field'],
            'dot' => ['my.field'],
            'over 63 characters' => [str_repeat('a', 64)],
            'trailing newline' => ["fieldName\n"],
        ];
    }

    #[DataProvider('invalidNameProvider')]
    public function testFieldNameThatIsNotAnIdentifierIsRefusedWithNoGeneratedFile(string $name): void
    {
        $classFile = PIMCORE_CLASS_DIRECTORY . '/DataObject/' . self::CLASS_NAME . '.php';

        try {
            $class = class_definition_from_layout(
                [field_node('input', ['name' => $name, 'title' => 'field'])],
                self::CLASS_NAME
            );
            dump_class_files($class, self::CLASS_NAME);
        } catch (\Throwable $refused) {
            $this->assertFileDoesNotExist($classFile, 'a refused definition must not leave a generated class file');

            return;
        }

        $this->fail('a field name that is not a plain identifier was accepted');
    }

    public function testFieldNamePayloadNeverSurvivesAsExecutableCode(): void
    {
        $payload = 'x; echo PWN_NAME;//';

        try {
            $class = class_definition_from_layout(
                [field_node('input', ['name' => $payload, 'title' => 'field'])],
                self::CLASS_NAME
            );
            $code = build_class_code($class);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);

            return;
        }

        $this->assertFalse(
            has_executable_marker($code, 'PWN_NAME'),
            'the field name became executable code in the generated class file'
        );
    }

    public function testClassificationStoreNameThatIsNotAnIdentifierIsRefused(): void
    {
        $payload = 'x; echo PWN_CS;//';
        $classFile = PIMCORE_CLASS_DIRECTORY . '/DataObject/' . self::CLASS_NAME . '.php';

        try {
            $class = class_definition_from_layout(
                [field_node('classificationstore', ['name' => $payload, 'title' => 'store'])],
                self::CLASS_NAME
            );
            dump_class_files($class, self::CLASS_NAME);
        } catch (\Throwable $refused) {
            $this->assertFileDoesNotExist($classFile, 'a refused definition must not leave a generated class file');

            return;
        }

        $this->fail('a classification store field name that is not a plain identifier was accepted');
    }

    public function testDisplayTitleCannotTerminateTheGeneratedComment(): void
    {
        $payload = '*/ echo PWN_TITLE; /*';

        try {
            $class = class_definition_from_layout(
                [field_node('input', ['name' => 'goodField', 'title' => $payload])],
                self::CLASS_NAME
            );
            $code = build_class_code($class);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);

            return;
        }

        $this->assertFalse(
            has_executable_marker($code, 'PWN_TITLE'),
            'a display title escaped a generated comment and became executable code'
        );
    }

    public function testLegacyAccessorAliasThatIsNotAnIdentifierIsRefused(): void
    {
        $payload = 'x; echo PWN_ALIAS;//';
        $classFile = PIMCORE_CLASS_DIRECTORY . '/DataObject/' . self::CLASS_NAME . '.php';

        try {
            $class = class_definition_from_layout(
                [field_node('input', ['name' => 'goodField', 'title' => 'field', 'legacyName' => $payload])],
                self::CLASS_NAME
            );
            dump_class_files($class, self::CLASS_NAME);
        } catch (\Throwable $refused) {
            $this->assertFileDoesNotExist($classFile, 'a refused definition must not leave a generated class file');

            return;
        }

        $this->fail('an accessor alias that is not a plain identifier was accepted');
    }

    public function testDisplayTitleCannotBreakOutOfTheGeneratedLabelData(): void
    {
        $payload = '"]; public function pwn(){ echo PWN_LABEL; } /*';

        try {
            $class = class_definition_from_layout(
                [field_node('input', ['name' => 'goodField', 'title' => $payload])],
                self::CLASS_NAME
            );
            $code = build_class_code($class);
        } catch (\Throwable $refused) {
            $this->addToAssertionCount(1);

            return;
        }

        $this->assertFalse(
            has_executable_marker($code, 'PWN_LABEL'),
            'a display title ended the generated string it is placed in and became executable code'
        );
    }
}
