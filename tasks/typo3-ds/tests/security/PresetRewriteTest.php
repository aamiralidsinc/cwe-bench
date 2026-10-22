<?php

declare(strict_types=1);

/*
 * The product ships a maintenance tool that rewrites an existing stored
 * definition from a preset document. A preset has not been through the form
 * framework's own validation, so the tool may either refuse it or store the
 * resulting definition only by passing it through the framework's persistence
 * path; rewriting the stored configuration by any other route changes it
 * without validation.
 */

namespace CweTests\Security;

use CweTests\FunctionalTestCase;
use PHPUnit\Framework\Attributes\Test;
use Symfony\Component\Console\Tester\CommandTester;
use TYPO3\CMS\Core\Database\ConnectionPool;
use TYPO3\CMS\Form\Command\ApplyFormDefinitionPresetCommand;
use TYPO3\CMS\Form\Domain\DTO\FormData;

final class PresetRewriteTest extends FunctionalTestCase
{
    private function fetchRow(int $uid): ?array
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

    private function runPreset(int $uid, array $preset): int
    {
        $file = tempnam(sys_get_temp_dir(), 'form-preset-') . '.json';
        file_put_contents($file, json_encode($preset, JSON_THROW_ON_ERROR));
        try {
            $tester = new CommandTester($this->get(ApplyFormDefinitionPresetCommand::class));
            $tester->execute(['uid' => (string)$uid, 'preset' => $file], []);
            return (int)$tester->getStatusCode();
        } finally {
            @unlink($file);
        }
    }

    /**
     * The preset is acceptable only in one of two shapes: the tool refuses it
     * and leaves the stored definition alone, or it stores the merged
     * definition through the framework's persistence path, which stores the
     * definition normalised the way the framework stores it. A configuration
     * written by any other route keeps the raw preset and therefore fails.
     */
    #[Test]
    public function applyingAPresetThatRewritesTheStoredDefinitionIsRefusedOrStoredThroughTheValidatedPath(): void
    {
        $before = $this->fetchRow(1);
        self::assertIsArray($before);
        $definition = json_decode($before['configuration'], true, 512, JSON_THROW_ON_ERROR);
        self::assertIsArray($definition);

        $preset = [
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
            'x-preset-marker' => 'injected-preset',
        ];

        $status = $this->runPreset(1, $preset);

        $after = $this->fetchRow(1);
        self::assertIsArray($after);
        if ($after['configuration'] === $before['configuration']) {
            self::assertNotSame(0, $status, 'The preset was neither refused nor persisted.');
            return;
        }

        self::assertSame(0, $status, 'The preset was persisted but the operation reported a failure.');
        $expectedConfiguration = json_encode(
            FormData::fromArray(array_replace($definition, $preset))->toArray(),
            JSON_THROW_ON_ERROR
        );
        self::assertSame(
            $expectedConfiguration,
            $after['configuration'],
            'The preset was stored without passing through the framework persistence path.'
        );
    }
}
