<?php

declare(strict_types=1);

namespace CweBench\MongoPhpLibrary\Security;

use MongoDB\Collection;
use MongoDB\Driver\Manager;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

/**
 * A collection handle resolved from a namespace must address exactly the database and
 * collection the namespace denotes: the database is the text before the first period and
 * the collection is everything after it.
 */
final class NamespaceResolutionSecurityTest extends TestCase
{
    private const URI = 'mongodb://127.0.0.1:27017/?serverSelectionTimeoutMS=100';

    private static Manager $manager;

    public static function setUpBeforeClass(): void
    {
        self::$manager = new Manager(self::URI);
    }

    /** @return array<string, array{string, string, string}> */
    public static function provideNamespaces(): array
    {
        return [
            'dotted collection' => ['prod.tenant7.orders', 'prod', 'tenant7.orders'],
            'dotted collection with several periods' => ['prod.a.b.c', 'prod', 'a.b.c'],
            'bucket files collection' => ['prod.fs.files', 'prod', 'fs.files'],
        ];
    }

    #[DataProvider('provideNamespaces')]
    public function testNamespaceResolvesToExactlyTheNamedCollection(string $namespace, string $databaseName, string $collectionName): void
    {
        $collection = Collection::fromNamespace(self::$manager, $namespace);

        self::assertSame($databaseName, $collection->getDatabaseName());
        self::assertSame($collectionName, $collection->getCollectionName());
        self::assertSame($namespace, $collection->getNamespace());
    }
}
