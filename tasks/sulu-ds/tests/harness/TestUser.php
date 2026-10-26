<?php

namespace Sulu\Task\Harness;

use Sulu\Bundle\SecurityBundle\Entity\User;

class TestUser extends User
{
    public function __construct(private int $testId, string $identifier, private string $testLocale = 'en')
    {
        parent::__construct();
        $this->setUsername($identifier);
    }

    public function getId()
    {
        return $this->testId;
    }

    public function getLocale()
    {
        return $this->testLocale;
    }
}
