<?php

namespace CweTests;

use Illuminate\Contracts\Debug\ExceptionHandler;
use Illuminate\Http\Request;
use Symfony\Component\HttpKernel\Exception\HttpExceptionInterface;

/**
 * What counts as a refusal (2026-10-16). A request is refused when the application answers it
 * as a client error (any 4xx), or the component reports a validation error, AND it caused no
 * side effect (each test checks its own side effects). The exception class and the exact status
 * are the fix's choice. A crash does NOT count: an exception the application would answer with
 * a server error (a null dereference, an undefined key, a generic exception) is not a refusal,
 * even though it happens to stop the request. Nor is 419: Livewire answers any TypeError raised
 * during a component update with 419 "Page Expired" (and uses it for corrupt payloads), so a 419
 * marks a crash, not a deliberate refusal.
 */
trait AssertsRefusal
{
    /** The status the application's own exception handler answers this exception with. */
    protected function statusForException(\Throwable $e): ?int
    {
        if ($e instanceof HttpExceptionInterface) {
            return $e->getStatusCode();
        }

        try {
            // Livewire calls are JSON requests, so render the exception the way one would be.
            $request = Request::create('/livewire/update', 'POST', server: [
                'HTTP_ACCEPT' => 'application/json',
                'HTTP_X_LIVEWIRE' => 'true',
            ]);

            // Livewire's test broker swaps in a "without exception handling" wrapper (which
            // rethrows) and does not put the real handler back when the call throws.
            $handler = $this->app->make(ExceptionHandler::class);
            if (property_exists($handler, 'originalHandler')) {
                $handler = (fn () => $this->originalHandler)->call($handler);
            }

            return $handler->render($request, $e)->getStatusCode();
        } catch (\Throwable) {
            return null;
        }
    }

    /** A deliberate client-error answer: any 4xx except 419 (see above). */
    protected function isRefusalStatus(?int $status): bool
    {
        return ($status !== null) && ($status >= 400) && ($status < 500) && ($status !== 419);
    }

    /** The status the Livewire test harness recorded for the last request of this component. */
    protected function componentStatus(mixed $component): ?int
    {
        try {
            return \Livewire\invade($component)->lastState->getResponse()->getStatusCode();
        } catch (\Throwable) {
            return null;
        }
    }

    /** The request was not answered with a crash (5xx, or Livewire's 419 for a TypeError). */
    protected function assertComponentDidNotCrash(mixed $component, string $what): void
    {
        $status = $this->componentStatus($component);

        $this->assertFalse(
            ($status === 419) || (($status !== null) && ($status >= 500)),
            sprintf('%s was answered with HTTP %s: a crash, not a refusal', $what, $status),
        );
    }

    protected function assertExceptionIsRefusal(\Throwable $e, string $what): void
    {
        $status = $this->statusForException($e);

        $this->assertTrue(
            $this->isRefusalStatus($status),
            sprintf(
                '%s was stopped by %s (%s), which the application answers with %s: a crash, not a refusal',
                $what,
                $e::class,
                $e->getMessage(),
                $status === null ? 'no response' : "HTTP {$status}",
            ),
        );
    }

    /** True when the returned Livewire component answered with a deliberate client error. */
    protected function componentAnsweredWithClientError(mixed $component): bool
    {
        return $this->isRefusalStatus($this->componentStatus($component));
    }

    /** True when the returned Livewire component carries at least one validation error. */
    protected function componentHasValidationErrors(mixed $component): bool
    {
        try {
            return $component->errors()->isNotEmpty();
        } catch (\Throwable) {
            return false;
        }
    }
}
