<?php
declare(strict_types=1);

/**
 * Test-side helpers shared by the hidden suites.
 *
 * Nothing here calls product code to decide what is safe: the SQL analysis is a small
 * tokenizer over the condition text, and the product objects are built by reflection so a
 * fix that adds constructor dependencies (e.g. a connection resolver) still works.
 */

namespace Pimcore\Bundle\StudioBackendBundle\Tests\Hidden\Support;

use Doctrine\DBAL\Connection;
use Doctrine\DBAL\Platforms\MySQLPlatform;
use Doctrine\DBAL\Query\QueryBuilder;
use Doctrine\DBAL\Result;
use Pimcore\Bundle\StaticResolverBundle\Db\DbResolverInterface;
use Pimcore\Bundle\StudioBackendBundle\ClassificationStore\ListingFilter\ConfigurationFieldFilter;
use Pimcore\Bundle\StudioBackendBundle\Filter\Mapper\CollectionParametersMapper;
use Pimcore\Bundle\StudioBackendBundle\Filter\MappedParameter\FilterParameter;
use Pimcore\Bundle\StudioBackendBundle\Listing\Filter\DateFilter;
use Pimcore\Bundle\StudioBackendBundle\Listing\Filter\EqualsFilter;
use Pimcore\Bundle\StudioBackendBundle\Listing\Filter\LikeFilter;
use Pimcore\Bundle\StudioBackendBundle\Listing\Filter\Loader\TaggedIteratorAdapter;
use Pimcore\Bundle\StudioBackendBundle\Listing\Service\ListingFilter;
use Pimcore\Bundle\StudioBackendBundle\MappedParameter\CollectionFilterParameter;
use Pimcore\Bundle\StudioBackendBundle\Translation\ListingFilter\TranslationLikeFilter;
use ReflectionClass;
use ReflectionNamedType;
use ReflectionParameter;

trait ProductTrait
{
    /** Raw SQL fragments a supplied name must never contribute (tokenised form). */
    protected const SQL_MARKER = 'OR ( SELECT 1 ) OR';

    /** Appended to a real column name: closes the quoting and adds a subquery. */
    protected const IDENTIFIER_ATTACK = '` OR (SELECT 1) OR `x';

    /** Appended to a real column name: would sit after the bound parameter if the name were reused in it. */
    protected const PARAMETER_ATTACK = '=qid OR (SELECT 1) OR qid';

    private array $capturedSql = [];

    private array $capturedParameters = [];

    private ?Connection $connection = null;

    /**
     * Build a product object without assuming its constructor shape.
     */
    protected function buildProduct(string $class, array $overrides = []): object
    {
        $reflection = new ReflectionClass($class);
        $constructor = $reflection->getConstructor();

        if ($constructor === null) {
            return $reflection->newInstance();
        }

        $arguments = [];
        foreach ($constructor->getParameters() as $parameter) {
            $arguments[] = $this->argumentFor($parameter, $overrides);
        }

        return $reflection->newInstanceArgs($arguments);
    }

    private function argumentFor(ReflectionParameter $parameter, array $overrides): mixed
    {
        $type = $parameter->getType();
        $name = $type instanceof ReflectionNamedType && !$type->isBuiltin() ? $type->getName() : null;

        if ($name !== null && array_key_exists($name, $overrides)) {
            return $overrides[$name];
        }

        if ($name !== null && interface_exists($name)) {
            if (is_a($name, DbResolverInterface::class, true)) {
                return $this->dbResolver();
            }

            return $this->makeEmpty($name);
        }

        if ($name !== null && class_exists($name)) {
            if (is_a($name, Connection::class, true)) {
                return $this->sqlConnection();
            }
            if (is_a($name, MySQLPlatform::class, true)) {
                return new MySQLPlatform();
            }
            $inner = new ReflectionClass($name);
            $innerConstructor = $inner->getConstructor();
            if ($innerConstructor === null || $innerConstructor->getNumberOfRequiredParameters() === 0) {
                return $inner->newInstance();
            }
        }

        if ($parameter->isDefaultValueAvailable()) {
            return $parameter->getDefaultValue();
        }

        return null;
    }

    protected function dbResolver(): DbResolverInterface
    {
        $connection = $this->sqlConnection();

        return $this->makeEmpty(DbResolverInterface::class, [
            'get' => $connection,
        ]);
    }

    protected function sqlConnection(): Connection
    {
        if ($this->connection !== null) {
            return $this->connection;
        }

        $result = $this->makeEmpty(Result::class, [
            'fetchAllAssociative' => [],
            'fetchAssociative' => false,
            'fetchOne' => 0,
            'fetchFirstColumn' => [],
            'rowCount' => 0,
        ]);

        $this->connection = $this->makeEmpty(Connection::class, [
            'getDatabasePlatform' => new MySQLPlatform(),
            'quoteIdentifier' => static fn (string $identifier): string => '`' . str_replace('`', '``', $identifier) . '`',
            'executeQuery' => function (string $sql, array $params = [], array $types = []) use ($result): Result {
                $this->capturedSql[] = $sql;
                $this->capturedParameters[] = $params;

                return $result;
            },
        ]);
        $this->connection->method('createQueryBuilder')->willReturnCallback(
            fn (): QueryBuilder => new QueryBuilder($this->connection)
        );

        return $this->connection;
    }

    /**
     * The shared listing dispatch every collection endpoint performs.
     */
    protected function applyListingFilters(array $columnFilters, object $listing, array $extraFilters = []): object
    {
        $filters = [
            $this->buildProduct(DateFilter::class),
            $this->buildProduct(EqualsFilter::class),
            $this->buildProduct(LikeFilter::class),
            $this->buildProduct(TranslationLikeFilter::class),
            $this->buildProduct(ConfigurationFieldFilter::class),
            ...$extraFilters,
        ];

        $parameter = new FilterParameter(columnFilters: $columnFilters);
        $mapped = (new CollectionParametersMapper())->map(
            new CollectionFilterParameter(filters: $parameter)
        );

        $dispatcher = new ListingFilter(new TaggedIteratorAdapter($filters));

        return $dispatcher->applyFilters($mapped, $listing);
    }

    /**
     * Runs a call that may legitimately refuse the request; the caller asserts on the SQL only.
     */
    protected function runAllowingRefusal(callable $call): mixed
    {
        try {
            return $call();
        } catch (\Throwable) {
            return null;
        }
    }

    /**
     * True when none of the supplied names contributes SQL syntax to the statement.
     *
     * Quoted identifiers (doubled backticks included) and string literals are replaced by
     * placeholder tokens, so a fragment that merely sits inside a quoted name is inert while the
     * same fragment outside any quoting is statement syntax.
     */
    protected function assertNoRawSql(string $sql, string $fragment = self::SQL_MARKER): void
    {
        $this->assertStringNotContainsString(
            $fragment,
            $this->syntaxOnly($sql),
            'a supplied name became SQL syntax: ' . $sql
        );
    }

    protected function syntaxOnly(string $sql): string
    {
        $out = '';
        foreach ($this->sqlTokens($sql) as [$type, $value]) {
            $out .= match ($type) {
                'quoted' => ' <ID> ',
                'literal' => ' <STR> ',
                default => ' ' . $value . ' ',
            };
        }

        return preg_replace('/\s+/', ' ', $out) ?? $out;
    }

    /**
     * Tokenise enough SQL to tell one quoted name apart from a quoted compound name.
     *
     * @return list<array{0: string, 1: string}>
     */
    protected function sqlTokens(string $sql): array
    {
        $tokens = [];
        $length = strlen($sql);
        $index = 0;

        while ($index < $length) {
            $char = $sql[$index];

            if ($char === "'" || $char === '"') {
                $quote = $char;
                $cursor = $index + 1;
                $value = '';
                while ($cursor < $length) {
                    if ($sql[$cursor] === '\\' && $cursor + 1 < $length) {
                        $value .= $sql[$cursor + 1];
                        $cursor += 2;
                        continue;
                    }
                    if ($sql[$cursor] === $quote) {
                        if ($cursor + 1 < $length && $sql[$cursor + 1] === $quote) {
                            $value .= $quote;
                            $cursor += 2;
                            continue;
                        }
                        break;
                    }
                    $value .= $sql[$cursor];
                    $cursor++;
                }
                $tokens[] = ['literal', $value];
                $index = $cursor + 1;
                continue;
            }

            if ($char === '`') {
                $cursor = $index + 1;
                $value = '';
                while ($cursor < $length) {
                    if ($sql[$cursor] === '`') {
                        if ($cursor + 1 < $length && $sql[$cursor + 1] === '`') {
                            $value .= '`';
                            $cursor += 2;
                            continue;
                        }
                        break;
                    }
                    $value .= $sql[$cursor];
                    $cursor++;
                }
                $tokens[] = ['quoted', $value];
                $index = $cursor + 1;
                continue;
            }

            if (preg_match('/\G[A-Za-z_][A-Za-z0-9_]*/', $sql, $match, 0, $index) === 1) {
                $tokens[] = ['word', $match[0]];
                $index += strlen($match[0]);
                continue;
            }

            $tokens[] = [$char === '.' ? 'dot' : 'other', $char];
            $index++;
        }

        return $tokens;
    }

    /**
     * The condition must reference the qualified name alias.field as two identifiers around a dot
     * (or as two bare words). A single quoted "alias.field" is a different name.
     */
    protected function assertQualifiedIdentifier(string $sql, string $alias, string $field): void
    {
        $tokens = $this->sqlTokens($sql);
        $count = count($tokens);

        for ($i = 0; $i + 2 < $count; $i++) {
            if ($tokens[$i][1] === $alias && $tokens[$i + 1][0] === 'dot' && $tokens[$i + 2][1] === $field) {
                $this->addToAssertionCount(1);

                return;
            }
        }

        $this->fail(sprintf('expected the qualified identifier %s.%s, got: %s', $alias, $field, $sql));
    }

    protected function assertColumnIdentifier(string $sql, string $column): void
    {
        foreach ($this->sqlTokens($sql) as $token) {
            if ($token[0] !== 'other' && $token[0] !== 'dot' && $token[1] === $column) {
                $this->addToAssertionCount(1);

                return;
            }
        }

        $this->fail(sprintf('expected the column identifier %s, got: %s', $column, $sql));
    }

    protected function capturedSql(): array
    {
        return $this->capturedSql;
    }

    protected function capturedParameters(): array
    {
        return $this->capturedParameters;
    }
}
