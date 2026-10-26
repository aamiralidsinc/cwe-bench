<?php

/**
 * Data fixtures shared by the hidden suites.
 *
 * Everything here is test bookkeeping: records are written and removed with plain SQL and the
 * expected values are literals, so a hardened product helper can never change an expectation.
 */

declare(strict_types=1);

use phpMyFAQ\Configuration;
use phpMyFAQ\Language;
use Symfony\Component\HttpFoundation\Session\Session;

final class FaqVisibilityFixture
{
    public const int CATEGORY = 1;

    public const int TAG = 7;

    public function __construct(public readonly Configuration $configuration)
    {
    }

    public static function boot(): self
    {
        \phpMyFAQ\Translation::create()
            ->setTranslationsDir(PMF_TRANSLATION_DIR)
            ->setDefaultLanguage('en')
            ->setCurrentLanguage('en')
            ->setMultiByteLanguage();

        $configuration = Configuration::getConfigurationInstance();
        $configuration->set('main.currentVersion', \phpMyFAQ\System::getVersion());
        $configuration->set('security.permLevel', 'basic');
        $configuration->set('api.enableAccess', 'true');
        $configuration->set('search.searchForSolutionId', 'true');

        $language = new Language($configuration, new Session());
        Language::$language = 'en';
        $configuration->setLanguage($language);

        return new self($configuration);
    }

    public function db(): mixed
    {
        return $this->configuration->getDb();
    }

    public function reset(): void
    {
        foreach ([
            'faqdata',
            'faqcategoryrelations',
            'faqdata_user',
            'faqdata_group',
            'faqvisits',
            'faqdata_tags',
            'faqtags',
            'faqcategories',
        ] as $table) {
            $this->db()->query('DELETE FROM ' . $table);
        }

        $this->db()->query(
            'INSERT INTO faqcategories (id, lang, parent_id, name, description, user_id, group_id, active, image, show_home) '
            . "VALUES (1, 'en', 0, 'Category', '', -1, -1, 'yes', '', 1)",
        );
        $this->db()->query(
            'INSERT INTO faqtags (tagging_id, tagging_name) VALUES (' . self::TAG . ", 'knowledge')",
        );
    }

    /**
     * Insert one record and return its marker.
     *
     * States:
     *   visible       enabled, default publication window
     *   scheduled     enabled, publication starts tomorrow
     *   expired       enabled, publication ended yesterday
     *   inactive      disabled, default publication window
     *   windowed      enabled, a window already open (started yesterday, ends tomorrow)
     */
    public function seed(int $id, string $state, string $marker, bool $sticky = false): string
    {
        $now = date('YmdHis');
        $tomorrow = date('YmdHis', strtotime('+1 day'));
        $yesterday = date('YmdHis', strtotime('-1 day'));

        [$active, $start, $end] = match ($state) {
            'visible' => ['yes', '00000000000000', '99991231235959'],
            'scheduled' => ['yes', $tomorrow, '99991231235959'],
            'expired' => ['yes', '00000000000000', $yesterday],
            'inactive' => ['no', '00000000000000', '99991231235959'],
            'windowed' => ['yes', $yesterday, $tomorrow],
            default => throw new InvalidArgumentException('unknown state: ' . $state),
        };

        $this->db()->query(sprintf(
            "INSERT INTO faqdata (id, lang, solution_id, revision_id, active, sticky, keywords, thema, content, "
            . "author, email, comment, updated, date_start, date_end, created, notes) VALUES "
            . "(%d, 'en', %d, 0, '%s', %d, 'K%s', 'T%s', 'A%s', 'U%s', '%s@example.test', 'y', '%s', '%s', '%s', '%s', 'N%s')",
            $id,
            $id + 1000,
            $active,
            $sticky ? 1 : 0,
            $marker,
            $marker,
            $marker,
            $marker,
            strtolower($marker),
            $now,
            $start,
            $end,
            $now,
            $marker,
        ));

        $this->db()->query(sprintf(
            "INSERT INTO faqcategoryrelations (category_id, category_lang, record_id, record_lang) VALUES (%d, 'en', %d, 'en')",
            self::CATEGORY,
            $id,
        ));
        $this->db()->query(sprintf(
            "INSERT INTO faqdata_user (record_id, user_id) VALUES (%d, -1)",
            $id,
        ));
        $this->db()->query(sprintf(
            "INSERT INTO faqvisits (id, lang, visits, last_visit) VALUES (%d, 'en', 3, '%s')",
            $id,
            $now,
        ));
        $this->db()->query(sprintf(
            'INSERT INTO faqdata_tags (record_id, tagging_id) VALUES (%d, %d)',
            $id,
            self::TAG,
        ));

        return $marker;
    }
}
