<?php

namespace Sulu\Task\Harness;

use Sulu\Bundle\PreviewBundle\Preview\Object\PreviewObjectProviderInterface;

class TestPreviewObjectProvider implements PreviewObjectProviderInterface
{
    public function __construct(private string $key)
    {
    }

    public function getObject($id, $locale)
    {
        return ['id' => $id, 'locale' => $locale];
    }

    public function getId($object)
    {
        return $object['id'];
    }

    public function setValues($object, $locale, array $data)
    {
    }

    public function setContext($object, $locale, array $context)
    {
        return $object;
    }

    public function serialize($object)
    {
        return \json_encode($object) ?: '{}';
    }

    public function deserialize($serializedObject, $objectClass)
    {
        return \json_decode($serializedObject, true);
    }

    public function getSecurityContext($id, $locale): ?string
    {
        if ('media' === $this->key) {
            return null;
        }

        $webspace = Resources::webspaceFor($id);

        return null === $webspace ? null : 'sulu.webspaces.' . $webspace;
    }
}
