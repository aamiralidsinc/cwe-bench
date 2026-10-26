<?php

namespace Sulu\Task\Harness;

use FOS\RestBundle\View\View;
use FOS\RestBundle\View\ViewHandlerInterface;
use Sulu\Bundle\PreviewBundle\Domain\Model\PreviewLinkInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Serialises a view the way the admin API does: the preview-link model is exposed through its
 * getters, so a response carries the token.
 */
class TestViewHandler implements ViewHandlerInterface
{
    public function supports(string $format): bool
    {
        return 'json' === $format;
    }

    public function registerHandler(string $format, callable $callable): void
    {
    }

    public function handle(View $view, ?Request $request = null)
    {
        $status = $view->getStatusCode() ?? Response::HTTP_OK;
        $headers = $view->getHeaders();
        $data = $view->getData();

        if ($data instanceof PreviewLinkInterface) {
            $lastVisit = $data->getLastVisit();
            $data = [
                'token' => $data->getToken(),
                'resourceKey' => $data->getResourceKey(),
                'resourceId' => $data->getResourceId(),
                'locale' => $data->getLocale(),
                'options' => $data->getOptions(),
                'visitCount' => $data->getVisitCount(),
                'lastVisit' => $lastVisit ? $lastVisit->format(\DATE_ATOM) : null,
            ];
        }

        if (null === $data) {
            return new Response('', $status, $headers);
        }

        return new JsonResponse($data, $status, $headers);
    }

    public function createRedirectResponse(View $view, string $location, string $format)
    {
        return new RedirectResponse($location, $view->getStatusCode() ?? Response::HTTP_FOUND);
    }

    public function createResponse(View $view, Request $request, string $format)
    {
        return $this->handle($view, $request);
    }
}
