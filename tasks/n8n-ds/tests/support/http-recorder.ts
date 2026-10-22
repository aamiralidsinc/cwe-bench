import http from 'node:http';
import nock from 'nock';

export type RecordedRequest = { url: string; method: string };

/**
 * A loopback HTTP server that records every request and answers with `body`.
 * Used as the destination of a URL-content value; a blocked attack leaves it
 * with no hits. Real loopback connections are allowed through nock only while
 * this server is running.
 */
export async function startHttpRecorder(body: string) {
	const requests: RecordedRequest[] = [];
	const server = http.createServer((req, res) => {
		requests.push({ url: req.url ?? '', method: req.method ?? '' });
		res.writeHead(200, { 'content-type': 'text/plain' });
		res.end(body);
	});

	await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
	const address = server.address();
	if (!address || typeof address === 'string') throw new Error('no http port');

	nock.enableNetConnect('127.0.0.1');

	const close = async () => {
		nock.disableNetConnect();
		await new Promise<void>((resolve) => server.close(() => resolve()));
	};

	return {
		baseUrl: `http://127.0.0.1:${address.port}`,
		requests,
		close,
	};
}

export type HttpRecorder = Awaited<ReturnType<typeof startHttpRecorder>>;
