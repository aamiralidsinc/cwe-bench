<?php

namespace Sulu\Task\Harness;

use Symfony\Component\Security\Core\Authentication\Token\Storage\TokenStorageInterface;
use Symfony\Component\Security\Core\Authorization\AuthorizationCheckerInterface;
use Sulu\Component\Security\Authorization\SecurityCondition;

/**
 * Answers permission questions the way the product's authority does: per security context and
 * permission, for the user that currently holds the security token.
 */
class TestAuthorizationChecker implements AuthorizationCheckerInterface
{
    public function __construct(private TokenStorageInterface $tokenStorage)
    {
    }

    public function isGranted($attribute, $subject = null): bool
    {
        if (!$subject instanceof SecurityCondition) {
            return true;
        }

        $token = $this->tokenStorage->getToken();
        $user = $token ? $token->getUser() : null;
        $identifier = \is_object($user) && \method_exists($user, 'getUserIdentifier')
            ? $user->getUserIdentifier()
            : (string) $user;

        return PermissionMap::granted($identifier, $subject->getSecurityContext(), (string) $attribute);
    }
}
