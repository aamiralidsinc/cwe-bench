<?php

declare(strict_types=1);

/*
 * Shared harness for the hidden tests of this task.
 *
 * The tests run against the real TYPO3 functional-test stack (database, DI
 * container, backend authentication) and drive the product through the same
 * classes a backend request or a CLI command uses. Everything the tests need
 * to compute an expected value or to clean up is derived here or in the test
 * itself; no product helper decides whether a test passes.
 */

namespace CweTests;

use TYPO3\CMS\Core\Core\SystemEnvironmentBuilder;
use TYPO3\CMS\Core\Database\ConnectionPool;
use TYPO3\CMS\Core\DataHandling\DataHandler;
use TYPO3\CMS\Core\Http\ServerRequest;
use TYPO3\CMS\Core\Localization\LanguageServiceFactory;
use TYPO3\CMS\Core\Utility\GeneralUtility;
use TYPO3\TestingFramework\Core\Functional\FunctionalTestCase as CoreFunctionalTestCase;

abstract class FunctionalTestCase extends CoreFunctionalTestCase
{
    protected array $coreExtensionsToLoad = ['form'];

    protected function setUp(): void
    {
        parent::setUp();
        $this->importCSVDataSet(__DIR__ . '/Fixtures/be_users.csv');
        $backendUser = $this->setUpBackendUser(1);
        $GLOBALS['LANG'] = $this->get(LanguageServiceFactory::class)->createFromUserPreferences($backendUser);
        $this->importCSVDataSet(__DIR__ . '/Fixtures/form_definition.csv');
        $GLOBALS['TYPO3_REQUEST'] = (new ServerRequest('https://localhost/'))
            ->withAttribute('applicationType', SystemEnvironmentBuilder::REQUESTTYPE_BE);
    }

    /**
     * A non-admin backend user who is allowed to select and modify records of
     * the form-definition table but has no other elevated role.
     */
    protected function actAsFormEditor(): void
    {
        $backendUser = $this->setUpBackendUser(4);
        $GLOBALS['LANG'] = $this->get(LanguageServiceFactory::class)->createFromUserPreferences($backendUser);
    }

    protected function newDataHandler(): DataHandler
    {
        return GeneralUtility::makeInstance(DataHandler::class);
    }

    /**
     * Read a stored definition including soft-deleted rows, without going
     * through any product repository that a fix may harden.
     */
    protected function fetchRowIncludingDeleted(int $uid): ?array
    {
        $queryBuilder = $this->get(ConnectionPool::class)->getQueryBuilderForTable('form_definition');
        $queryBuilder->getRestrictions()->removeAll();
        $row = $queryBuilder
            ->select('*')
            ->from('form_definition')
            ->where($queryBuilder->expr()->eq('uid', $queryBuilder->createNamedParameter($uid)))
            ->executeQuery()
            ->fetchAssociative();
        return $row === false ? null : $row;
    }

    protected function countRowsByIdentifier(string $identifier): int
    {
        $queryBuilder = $this->get(ConnectionPool::class)->getQueryBuilderForTable('form_definition');
        return (int)$queryBuilder
            ->count('uid')
            ->from('form_definition')
            ->where($queryBuilder->expr()->eq('identifier', $queryBuilder->createNamedParameter($identifier)))
            ->executeQuery()
            ->fetchOne();
    }

    /**
     * A complete, harmlessly-valued form definition used as the stored payload
     * of an attack attempt. It is stored as JSON exactly the way the product
     * stores configurations.
     */
    protected function attackConfiguration(string $identifier): string
    {
        return json_encode([
            'identifier' => $identifier,
            'type' => 'Form',
            'label' => 'Injected Form',
            'prototypeName' => 'standard',
            'renderingOptions' => [],
            'finishers' => [
                [
                    'identifier' => 'SaveToDatabase',
                    'options' => [
                        'table' => 'fe_users',
                        'mode' => 'insert',
                        'elements' => [],
                        'databaseColumnMappings' => [
                            'username' => ['value' => 'injected'],
                        ],
                    ],
                ],
            ],
            'renderables' => [],
            'variants' => [],
        ], JSON_THROW_ON_ERROR);
    }

    /**
     * A complete, harmless form definition array, as the form editor and the
     * persistence manager hand it to the storage layer.
     */
    protected function formDefinitionArray(string $identifier, string $label): array
    {
        return [
            'identifier' => $identifier,
            'type' => 'Form',
            'label' => $label,
            'prototypeName' => 'standard',
            'renderingOptions' => [],
            'finishers' => [
                [
                    'identifier' => 'Confirmation',
                    'options' => ['message' => 'Thank you'],
                ],
            ],
            'renderables' => [
                [
                    'identifier' => 'page-1',
                    'type' => 'Page',
                    'label' => 'Page 1',
                    'renderables' => [
                        [
                            'identifier' => 'text-1',
                            'type' => 'Text',
                            'label' => 'Text',
                        ],
                    ],
                ],
            ],
            'variants' => [],
        ];
    }
}
