<?php
declare(strict_types=1);

/*
 * Shared harness for the hidden tests.
 *
 * The class-generation path is driven exactly as production does it: the definition
 * document (the JSON layout an import command writes) is applied through the
 * project's own implementation loaders via Service::generateLayoutTreeFromArray(),
 * and the resulting ClassDefinition is handed to PHPClassDumper / ClassBuilder.
 *
 * The database DDL path is driven through the real Dao classes and the real shared
 * DDL trait. The database connection is a recording double that answers per table
 * the way MySQL would (column lists, information_schema index lookups) and records
 * the statements the product code executes. Expected values and clean-ups are
 * computed here, in the tests, never with product helpers.
 */

namespace Pimcore\Tests\Cwe;

use Doctrine\DBAL\Cache\ArrayResult;
use Doctrine\DBAL\Cache\QueryCacheProfile;
use Doctrine\DBAL\Connection;
use Doctrine\DBAL\Driver\PDO\MySQL\Driver as MySQLDriver;
use Doctrine\DBAL\Platforms\AbstractPlatform;
use Doctrine\DBAL\Platforms\MySQLPlatform;
use Doctrine\DBAL\Result;
use Pimcore\DataObject\ClassBuilder\ClassBuilder;
use Pimcore\DataObject\ClassBuilder\FieldDefinitionBuilder;
use Pimcore\DataObject\ClassBuilder\FieldDefinitionDocBlockBuilder;
use Pimcore\DataObject\ClassBuilder\FieldDefinitionPropertiesBuilder;
use Pimcore\DataObject\ClassBuilder\ListingClassBuilder;
use Pimcore\DataObject\ClassBuilder\ListingClassFieldDefinitionBuilder;
use Pimcore\DataObject\ClassBuilder\PHPClassDumper;
use Pimcore\Loader\ImplementationLoader\PrefixLoader;
use Pimcore\Model\DataObject\ClassDefinition;
use Pimcore\Model\DataObject\ClassDefinition\Data;
use Pimcore\Model\DataObject\ClassDefinition\Loader\DataLoader;
use Pimcore\Model\DataObject\ClassDefinition\Loader\LayoutLoader;
use Pimcore\Model\DataObject\ClassDefinition\Service;
use Symfony\Component\Config\Loader\LoaderInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\Filesystem\Filesystem;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Bundle\BundleInterface;
use Symfony\Component\HttpKernel\KernelInterface;

/**
 * The definition importer resolves field/layout implementations from the container.
 * A minimal kernel + container with the project's real loaders is enough; no routes,
 * bundles or services of the application are involved.
 */
final class StubKernel implements KernelInterface
{
    public function __construct(private readonly ContainerInterface $container)
    {
    }

    public function registerBundles(): iterable
    {
        return [];
    }

    public function registerContainerConfiguration(LoaderInterface $loader): void
    {
    }

    public function boot(): void
    {
    }

    public function shutdown(): void
    {
    }

    public function getBundles(): array
    {
        return [];
    }

    public function getBundle(string $name): BundleInterface
    {
        throw new \RuntimeException('No bundles in the test kernel');
    }

    public function locateResource(string $name): string
    {
        throw new \RuntimeException('No bundles in the test kernel');
    }

    public function getEnvironment(): string
    {
        return 'test';
    }

    public function isDebug(): bool
    {
        return false;
    }

    public function getProjectDir(): string
    {
        return '/workspace';
    }

    public function getContainer(): ContainerInterface
    {
        return $this->container;
    }

    public function getStartTime(): float
    {
        return 0.0;
    }

    public function getCacheDir(): string
    {
        return '/tmp/pimcore-task-var/cache';
    }

    public function getBuildDir(): string
    {
        return '/tmp/pimcore-task-var/cache';
    }

    public function getLogDir(): string
    {
        return '/tmp/pimcore-task-var/log';
    }

    public function getCharset(): string
    {
        return 'UTF-8';
    }

    public function handle(Request $request, int $type = self::MAIN_REQUEST, bool $catch = true): Response
    {
        throw new \RuntimeException('No HTTP stack in the test kernel');
    }
}

/**
 * Doctrine connection double: answers the two catalogue lookups the DDL code makes
 * and records every statement. quoteIdentifier() is the real MySQL platform
 * implementation, so quoting behaviour is the production behaviour.
 */
final class RecordingConnection extends Connection
{
    /** @var string[] */
    public array $queries = [];

    /** @var array<string, array<string, bool>> table => index name => exists */
    public array $existingIndexes = [];

    public function __construct()
    {
        parent::__construct([], new MySQLDriver());
    }

    public function getDatabasePlatform(): AbstractPlatform
    {
        return new MySQLPlatform();
    }

    public function executeQuery(
        string $sql,
        array $params = [],
        array $types = [],
        ?QueryCacheProfile $qcp = null,
    ): Result {
        $this->queries[] = $sql;

        return new Result(new ArrayResult(['x'], []), $this);
    }

    public function fetchFirstColumn(string $query, array $params = [], array $types = []): array
    {
        if (str_contains($query, 'information_schema.statistics')) {
            $table = (string) ($params[0] ?? '');
            $index = (string) ($params[1] ?? '');

            return isset($this->existingIndexes[$table][$index]) ? [1] : [];
        }

        return [];
    }

    public function fetchAllAssociative(string $query, array $params = [], array $types = []): array
    {
        return [];
    }
}

/**
 * Subclass of the real class-definition Dao that exposes the DDL steps and answers
 * the table catalogue like MySQL would. Only the catalogue/cache lookups are
 * answered here; the DDL construction itself is the product code.
 */
class ClassDefinitionDaoProbe extends \Pimcore\Model\DataObject\ClassDefinition\Dao
{
    /** @var array<string, string[]> table => column names */
    public array $columns = [];

    public function __construct()
    {
        $this->db = new RecordingConnection();
    }

    public function getValidTableColumns(string $table, bool $cache = true, bool $primaryKeyColumnsOnly = false): array
    {
        return $this->columns[$table] ?? [];
    }

    public function resetValidTableColumnsCache(string $table): void
    {
    }

    public function addColumnStatement(string $table, string $column, string $type, string $default = '', string $null = 'NULL', string $comment = ''): void
    {
        $this->addModifyColumn($table, $column, $type, $default, $null, $comment);
    }

    public function addIndexStatement(Data $field, string $table, string $columnTypeGetter = 'getColumnType', bool $considerUniqueIndex = false, bool $isLocalized = false, bool $isFieldcollection = false): void
    {
        $this->addIndexToField($field, $table, $columnTypeGetter, $considerUniqueIndex, $isLocalized, $isFieldcollection);
    }

    public function dropUnusedColumns(string $table, array $columnsToRemove, array $protectedColumns): void
    {
        $this->removeUnusedColumns($table, $columnsToRemove, $protectedColumns);
    }

    /**
     * @return string[]
     */
    public function recordedQueries(): array
    {
        return $this->db->queries;
    }

    public function connection(): RecordingConnection
    {
        /** @var RecordingConnection $db */
        $db = $this->db;

        return $db;
    }
}

/**
 * Subclass of the real objectbrick definition Dao, which carries its own index-drop
 * implementation instead of using the shared trait.
 */
final class ObjectbrickDaoProbe extends \Pimcore\Model\DataObject\Objectbrick\Definition\Dao
{
    public function __construct()
    {
        $this->db = new RecordingConnection();
    }

    public function resetValidTableColumnsCache(string $table): void
    {
    }

    public function dropIndexStatements(string $table, array $columnsToRemove, array $protectedColumns): void
    {
        $this->removeIndices($table, $columnsToRemove, $protectedColumns);
    }

    /**
     * @return string[]
     */
    public function recordedQueries(): array
    {
        return $this->db->queries;
    }
}

function install_import_environment(): void
{
    static $installed = false;
    if ($installed) {
        return;
    }

    $container = new ContainerBuilder();
    $container->set(
        'pimcore.implementation_loader.object.data',
        new DataLoader([new PrefixLoader(['Pimcore\\Model\\DataObject\\ClassDefinition\\Data\\'])])
    );
    $container->set(
        'pimcore.implementation_loader.object.layout',
        new LayoutLoader([new PrefixLoader(['Pimcore\\Model\\DataObject\\ClassDefinition\\Layout\\'])])
    );

    \Pimcore::setKernel(new StubKernel($container));
    $installed = true;
}

/**
 * A leaf field entry as it appears in a class definition document.
 *
 * @param array<string, mixed> $properties
 * @return array<string, mixed>
 */
function field_node(string $fieldtype, array $properties): array
{
    return array_merge(['datatype' => 'data', 'fieldtype' => $fieldtype], $properties);
}

/**
 * Apply a definition document exactly as the import command does and return the
 * resulting class definition.
 *
 * @param array<int, array<string, mixed>> $children
 */
function class_definition_from_layout(array $children, string $className = 'TaskClass', array $classProperties = []): ClassDefinition
{
    install_import_environment();

    $layout = [
        'datatype' => 'layout',
        'fieldtype' => 'panel',
        'name' => 'pimcore_root',
        'type' => null,
        'children' => array_values($children),
    ];

    $tree = Service::generateLayoutTreeFromArray($layout, true);
    if (!$tree instanceof \Pimcore\Model\DataObject\ClassDefinition\Layout) {
        throw new \RuntimeException('definition document did not produce a layout');
    }

    $class = new ClassDefinition();
    $class->setName($className);
    foreach ($classProperties as $property => $value) {
        $setter = 'set' . ucfirst((string) $property);
        if (method_exists($class, $setter)) {
            $class->{$setter}($value);
        }
    }
    $class->setLayoutDefinitions($tree);

    return $class;
}

function build_class_code(ClassDefinition $class): string
{
    $builder = new ClassBuilder(
        new FieldDefinitionDocBlockBuilder(),
        new FieldDefinitionPropertiesBuilder(),
        new FieldDefinitionBuilder()
    );

    return $builder->buildClass($class);
}

function build_listing_code(ClassDefinition $class): string
{
    $builder = new ListingClassBuilder(new ListingClassFieldDefinitionBuilder());

    return $builder->buildListingClass($class);
}

/**
 * Run the production dump step and return the path it wrote (the path is computed
 * here from the class name, not read back through product code).
 */
function dump_class_files(ClassDefinition $class, string $className = 'TaskClass'): string
{
    $builder = new ClassBuilder(
        new FieldDefinitionDocBlockBuilder(),
        new FieldDefinitionPropertiesBuilder(),
        new FieldDefinitionBuilder()
    );
    $dumper = new PHPClassDumper(
        $builder,
        new ListingClassBuilder(new ListingClassFieldDefinitionBuilder()),
        new Filesystem()
    );
    $dumper->dumpPHPClasses($class);

    return PIMCORE_CLASS_DIRECTORY . '/DataObject/' . ucfirst($className) . '.php';
}

function clear_generated_files(): void
{
    $dir = PIMCORE_CLASS_DIRECTORY . '/DataObject';
    if (!is_dir($dir)) {
        return;
    }
    foreach (glob($dir . '/*.php') ?: [] as $file) {
        @unlink($file);
    }
    foreach (glob($dir . '/*/Listing.php') ?: [] as $file) {
        @unlink($file);
    }
}

/**
 * True when the marker appears anywhere in the token stream except comments and
 * string literals: that is the "became executable code / structure" test.
 */
function has_executable_marker(string $code, string $marker): bool
{
    if ($marker === '') {
        return false;
    }

    foreach (token_get_all($code) as $token) {
        if (is_array($token)) {
            [$id, $text] = $token;
            if (in_array($id, [
                T_COMMENT,
                T_DOC_COMMENT,
                T_CONSTANT_ENCAPSED_STRING,
                T_ENCAPSED_AND_WHITESPACE,
                T_INLINE_HTML,
                T_WHITESPACE,
            ], true)) {
                continue;
            }
            if (stripos($text, $marker) !== false) {
                return true;
            }
            continue;
        }
        if (stripos($token, $marker) !== false) {
            return true;
        }
    }

    return false;
}

/**
 * Values of the string literals in generated code, with their quotes removed.
 *
 * @return string[]
 */
function string_literal_values(string $code): array
{
    $out = [];
    foreach (token_get_all($code) as $token) {
        if (!is_array($token) || $token[0] !== T_CONSTANT_ENCAPSED_STRING) {
            continue;
        }
        $text = $token[1];
        $quote = $text[0] ?? '';
        $inner = substr($text, 1, -1);
        if ($quote === "'") {
            $out[] = str_replace(['\\\\', "\\'"], ['\\', "'"], $inner);
        } elseif ($quote === '"') {
            $out[] = stripcslashes($inner);
        } else {
            $out[] = $inner;
        }
    }

    return $out;
}

/**
 * Remove quoted identifiers / string literals from a statement so that only the
 * SQL structure is left. A value that stayed inside an identifier or literal is
 * gone; a value that broke out is still visible.
 */
function sql_structure(string $sql): string
{
    $out = '';
    $length = strlen($sql);
    $i = 0;

    while ($i < $length) {
        $char = $sql[$i];

        if ($char === '`' || $char === '"' || $char === "'") {
            $quote = $char;
            ++$i;
            while ($i < $length) {
                if (($quote === "'" || $quote === '"') && $sql[$i] === '\\') {
                    $i += 2;
                    continue;
                }
                if ($sql[$i] === $quote) {
                    if ($i + 1 < $length && $sql[$i + 1] === $quote) {
                        $i += 2;
                        continue;
                    }
                    ++$i;
                    break;
                }
                ++$i;
            }
            $out .= ' ';
            continue;
        }

        $out .= $char;
        ++$i;
    }

    return $out;
}

/**
 * @param string[] $queries
 */
function queries_contain_bare_marker(array $queries, string $marker): bool
{
    foreach ($queries as $query) {
        if (stripos(sql_structure($query), $marker) !== false) {
            return true;
        }
    }

    return false;
}
