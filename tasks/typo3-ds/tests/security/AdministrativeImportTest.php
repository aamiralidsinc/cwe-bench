<?php

declare(strict_types=1);

/*
 * The product ships an administrative tool that ingests a document of form
 * definitions. A document that arrives this way has not been through the form
 * framework's own validation, so the tool may either refuse it or store each
 * definition only by passing it through the framework's persistence path;
 * storing it by any other route changes the stored set without validation.
 */

namespace CweTests\Security;

use CweTests\FunctionalTestCase;
use PHPUnit\Framework\Attributes\Test;
use Symfony\Component\Console\Tester\CommandTester;
use TYPO3\CMS\Core\Database\ConnectionPool;
use TYPO3\CMS\Form\Command\ImportFormDefinitionsCommand;
use TYPO3\CMS\Form\Domain\DTO\FormData;

final class AdministrativeImportTest extends FunctionalTestCase
{
    private function runImport(array $records): int
    {
        $file = tempnam(sys_get_temp_dir(), 'form-export-') . '.json';
        file_put_contents($file, json_encode($records, JSON_THROW_ON_ERROR));
        try {
            $tester = new CommandTester($this->get(ImportFormDefinitionsCommand::class));
            $tester->execute(['file' => $file], []);
            return (int)$tester->getStatusCode();
        } finally {
            @unlink($file);
        }
    }

    private function fetchRowByIdentifier(string $identifier): ?array
    {
        $queryBuilder = $this->get(ConnectionPool::class)->getQueryBuilderForTable('form_definition');
        $queryBuilder->getRestrictions()->removeAll();
        $row = $queryBuilder
            ->select('*')
            ->from('form_definition')
            ->where($queryBuilder->expr()->eq('identifier', $queryBuilder->createNamedParameter($identifier)))
            ->executeQuery()
            ->fetchAssociative();
        return $row === false ? null : $row;
    }

    /**
     * The import is acceptable only in one of two shapes: it refuses the
     * definition and stores nothing, or it stores the definition through the
     * framework's persistence path, which stores the definition normalised the
     * way the framework stores it. A definition written by any other route is
     * stored unvalidated and therefore fails.
     *
     * @param array|string $configuration Nested configuration, or its serialised form
     */
    private function assertRefusedOrStoredThroughTheValidatedPath(string $identifier, array|string $configuration): void
    {
        $status = $this->runImport([
            [
                'identifier' => $identifier,
                'label' => 'Imported',
                'configuration' => $configuration,
            ],
        ]);

        $row = $this->fetchRowByIdentifier($identifier);
        if ($row === null) {
            self::assertNotSame(0, $status, 'The import neither refused the definition nor stored it.');
            return;
        }

        self::assertSame(0, $status, 'The import stored the definition but did not report success.');
        $definition = is_string($configuration)
            ? json_decode($configuration, true, 512, JSON_THROW_ON_ERROR)
            : $configuration;
        $expectedConfiguration = json_encode(
            FormData::fromArray($definition)->toArray(),
            JSON_THROW_ON_ERROR
        );
        self::assertSame(
            $expectedConfiguration,
            $row['configuration'],
            'The imported definition was stored without passing through the framework persistence path.'
        );
    }

    #[Test]
    public function importingANestedConfigurationIsRefusedOrStoredThroughTheValidatedPath(): void
    {
        $identifier = 'cwe-imported-nested';
        $this->assertRefusedOrStoredThroughTheValidatedPath($identifier, [
            'identifier' => $identifier,
            'type' => 'Form',
            'label' => 'Imported',
            'prototypeName' => 'standard',
            'finishers' => [
                ['identifier' => 'SaveToDatabase', 'options' => ['table' => 'fe_users', 'mode' => 'insert']],
            ],
            'renderables' => [],
        ]);
    }

    #[Test]
    public function importingASerializedConfigurationIsRefusedOrStoredThroughTheValidatedPath(): void
    {
        $identifier = 'cwe-imported-serialized';
        $this->assertRefusedOrStoredThroughTheValidatedPath($identifier, json_encode([
            'identifier' => $identifier,
            'type' => 'Form',
            'label' => 'Imported',
            'prototypeName' => 'standard',
            'finishers' => [
                ['identifier' => 'SaveToDatabase', 'options' => ['table' => 'fe_users', 'mode' => 'insert']],
            ],
            'renderables' => [],
        ], JSON_THROW_ON_ERROR));
    }
}
