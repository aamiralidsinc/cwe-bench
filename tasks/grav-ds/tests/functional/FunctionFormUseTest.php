<?php

use CweTests\SandboxTestCase;

/**
 * The equal-named function forms of the casting helpers are part of the
 * template surface content already uses. A guard that only covers the filter
 * registration, or that changes the helper's call signature without updating
 * the function registration, must not break them.
 */
final class FunctionFormUseTest extends SandboxTestCase
{
    public function testStringFunctionScalar(): void
    {
        self::assertSame('123', $this->renderString('{{ string(123) }}'));
    }

    public function testStringFunctionHeaderValue(): void
    {
        self::assertSame('Hello', $this->renderPageBody('{{ string(header.title) }}'));
    }

    public function testArrayFunctionPlainList(): void
    {
        self::assertSame('[1,2]', $this->renderString('{{ array([1,2])|json_encode|raw }}'));
    }
}
