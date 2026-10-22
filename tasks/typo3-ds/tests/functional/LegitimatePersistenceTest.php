<?php

declare(strict_types=1);

/*
 * The forms feature must keep working through its own persistence path: the
 * form manager/editor create and update forms, remove them, restore a removed
 * form, and the transfer command moves file-based forms into database storage.
 */

namespace CweTests\Functional;

use CweTests\FunctionalTestCase;
use PHPUnit\Framework\Attributes\Test;
use Symfony\Component\Console\Tester\CommandTester;
use TYPO3\CMS\Form\Command\RestoreFormDefinitionCommand;
use TYPO3\CMS\Form\Command\TransferFormDefinitionCommand;
use TYPO3\CMS\Form\Mvc\Persistence\FormPersistenceManagerInterface;

final class LegitimatePersistenceTest extends FunctionalTestCase
{
    protected array $testExtensionsToLoad = [
        __DIR__ . '/Fixtures/Extensions/test_form_persistence',
    ];

    private function persistenceManager(): FormPersistenceManagerInterface
    {
        return $this->get(FormPersistenceManagerInterface::class);
    }

    #[Test]
    public function theFormManagerCanCreateANewFormDefinition(): void
    {
        $manager = $this->persistenceManager();
        $persistenceIdentifier = $manager->getUniquePersistenceIdentifier('database', 'legit-created-form', '0');

        $saved = $manager->save(
            $persistenceIdentifier,
            $this->formDefinitionArray('legit-created-form', 'Legit Created Form'),
            [],
            '0',
        );

        $uid = (int)$saved->identifier;
        self::assertGreaterThan(0, $uid, 'saving a new form returned no record id');
        $row = $this->fetchRowIncludingDeleted($uid);
        self::assertIsArray($row);
        self::assertSame('legit-created-form', $row['identifier']);
        self::assertSame('Legit Created Form', $row['label']);
        self::assertSame(0, (int)$row['deleted']);

        $loaded = $manager->load((string)$uid);
        self::assertSame('legit-created-form', $loaded['identifier']);
        self::assertSame('Legit Created Form', $loaded['label']);
    }

    #[Test]
    public function theFormManagerCanUpdateAnExistingFormDefinition(): void
    {
        $manager = $this->persistenceManager();

        $manager->save(
            '1',
            $this->formDefinitionArray('crud-test-form', 'Updated By The Form Manager'),
            [],
            '0',
        );

        $row = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($row);
        self::assertSame('Updated By The Form Manager', $row['label']);
        self::assertSame(0, (int)$row['deleted']);

        $loaded = $manager->load('1');
        self::assertSame('Updated By The Form Manager', $loaded['label']);
    }

    #[Test]
    public function theFormManagerCanRemoveAFormDefinition(): void
    {
        $manager = $this->persistenceManager();
        $manager->delete('1', []);

        $row = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($row);
        self::assertSame(1, (int)$row['deleted'], 'the form manager did not remove the definition');
    }

    #[Test]
    public function aFormRemovedThroughTheManagerCanBeRestoredByTheRestoreTool(): void
    {
        $manager = $this->persistenceManager();
        $manager->delete('1', []);
        self::assertSame(1, (int)$this->fetchRowIncludingDeleted(1)['deleted']);

        $tester = new CommandTester($this->get(RestoreFormDefinitionCommand::class));
        $tester->execute(['uid' => '1'], []);

        self::assertSame(0, (int)$tester->getStatusCode(), 'the restore tool reported a failure');
        $row = $this->fetchRowIncludingDeleted(1);
        self::assertIsArray($row);
        self::assertSame(0, (int)$row['deleted'], 'the restore tool did not restore the definition');
    }

    #[Test]
    public function theFormManagerCanSaveADefinitionContainingASaveToDatabaseFinisher(): void
    {
        // A stored definition may contain any configuration the form setup
        // allows. Saving one through the framework's own path must keep
        // storing it unchanged, including a database finisher and its options.
        $manager = $this->persistenceManager();
        $definition = $this->formDefinitionArray('legit-database-form', 'Legit Database Form');
        $definition['finishers'] = [
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
        ];

        $persistenceIdentifier = $manager->getUniquePersistenceIdentifier('database', 'legit-database-form', '0');
        $saved = $manager->save($persistenceIdentifier, $definition, [], '0');

        $uid = (int)$saved->identifier;
        self::assertGreaterThan(0, $uid, 'saving a new form returned no record id');
        $row = $this->fetchRowIncludingDeleted($uid);
        self::assertIsArray($row);
        $stored = json_decode($row['configuration'], true, 512, JSON_THROW_ON_ERROR);
        self::assertSame('SaveToDatabase', $stored['finishers'][0]['identifier'] ?? null);
        self::assertSame('fe_users', $stored['finishers'][0]['options']['table'] ?? null);

        $loaded = $manager->load((string)$uid);
        self::assertSame('SaveToDatabase', $loaded['finishers'][0]['identifier'] ?? null);
    }

    #[Test]
    public function theTransferCommandStoresAFileBasedFormInTheDatabase(): void
    {
        $tester = new CommandTester($this->get(TransferFormDefinitionCommand::class));
        $tester->execute([
            '--source' => 'extension',
            '--target' => 'database',
            '--form-identifier' => 'test-extension-form',
        ], []);

        self::assertSame(0, (int)$tester->getStatusCode(), 'the transfer command reported a failure');
        self::assertSame(1, $this->countRowsByIdentifier('test-extension-form_1'), 'the transferred form was not stored');

        $manager = $this->persistenceManager();
        $forms = $manager->listForms([], new \TYPO3\CMS\Form\Domain\DTO\SearchCriteria());
        $identifiers = array_map(static fn($form) => $form->identifier, $forms);
        self::assertContains('test-extension-form_1', $identifiers, 'the transferred form is not listed by the form manager');
    }
}
