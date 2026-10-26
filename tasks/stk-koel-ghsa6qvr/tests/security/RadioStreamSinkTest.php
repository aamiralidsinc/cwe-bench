<?php

namespace Tests\Hidden;

use App\Services\Radio\RadioStreamProxy;
use PHPUnit\Framework\Attributes\Test;
use Throwable;

class RadioStreamSinkTest extends HiddenTestCase
{
    #[Test]
    public function doesNotOpenAStreamToAnInternalAddress(): void
    {
        $this->useFakeHttpStream(['*' => 'INTERNAL-SECRET']);

        try {
            $stream = app(RadioStreamProxy::class)->openStream('http://127.0.0.1:8080/stream');

            if (is_resource($stream)) {
                fclose($stream);
            }
        } catch (Throwable) {
            // a refusal is fine; the point is that nothing was opened
        }

        self::assertSame([], FakeHttpStream::openedTo('127.0.0.1'));
    }
}
