<?php

namespace Tests\Hidden;

use App\Services\Radio\RadioStreamProxy;
use PHPUnit\Framework\Attributes\Test;

class RadioStreamFlowTest extends HiddenTestCase
{
    #[Test]
    public function opensAPublicStream(): void
    {
        $audio = str_repeat('A', 4096);
        $this->useFakeHttpStream(['http://11.11.11.11/stream' => $audio]);

        $stream = app(RadioStreamProxy::class)->openStream('http://11.11.11.11/stream');

        self::assertIsResource($stream);
        self::assertSame($audio, stream_get_contents($stream));
        fclose($stream);
        self::assertNotSame([], FakeHttpStream::openedTo('11.11.11.11'));
    }
}
