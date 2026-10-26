<?php
/**
 * Functional-suite transport stub. Only the functional cases that opt in through
 * CRAFT_TEST_GUZZLE_MOCK use it; every other case talks to the real local fixtures.
 */
if (!getenv('CRAFT_TEST_GUZZLE_MOCK')) {
    return [];
}

use GuzzleHttp\Promise\Create;
use GuzzleHttp\Psr7\Response;

return [
    'handler' => static function ($request, array $options) {
        $uri = (string)$request->getUri();

        if (str_ends_with($uri, '/redirect.txt')) {
            return Create::promiseFor(new Response(302, [
                'Location' => 'http://assets.example.test/final.txt',
            ]));
        }

        $body = 'MOCK-ASSET-MARKER-42';

        if (isset($options['sink'])) {
            $sink = $options['sink'];
            if (is_resource($sink)) {
                fwrite($sink, $body);
            } elseif (is_string($sink)) {
                file_put_contents($sink, $body);
            }
        }

        return Create::promiseFor(new Response(200, ['Content-Type' => 'text/plain'], $body));
    },
];
