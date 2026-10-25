package wsbench.support;

import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.util.concurrent.atomic.AtomicInteger;

import com.sun.net.httpserver.HttpServer;

/**
 * A local HTTP listener that records every delivered SOAP message. The port and host
 * are real; nothing leaves the machine.
 */
public final class HttpVictim implements AutoCloseable {

	private final HttpServer server;

	private final String host;

	public final AtomicInteger hits = new AtomicInteger();

	private HttpVictim(HttpServer server, String host) {
		this.server = server;
		this.host = host;
	}

	public static HttpVictim startLoopback() throws Exception {
		return start("127.0.0.1");
	}

	public static HttpVictim startIpv6Loopback() throws Exception {
		return start("::1");
	}

	public static HttpVictim startAnyLocal() throws Exception {
		return start("0.0.0.0");
	}

	private static HttpVictim start(String address) throws Exception {
		InetAddress bind = InetAddress.getByName(address);
		HttpServer server = HttpServer.create(new InetSocketAddress(bind, 0), 0);
		HttpVictim victim = new HttpVictim(server, address);
		server.createContext("/", (exchange) -> {
			victim.hits.incrementAndGet();
			byte[] response = "<Received/>".getBytes(java.nio.charset.StandardCharsets.UTF_8);
			exchange.getResponseHeaders().add("Content-Type", "text/xml");
			exchange.sendResponseHeaders(200, response.length);
			exchange.getResponseBody().write(response);
			exchange.close();
		});
		server.start();
		return victim;
	}

	public int port() {
		return this.server.getAddress().getPort();
	}

	public String address(String hostOverride) {
		return hostOverride + ":" + port() + "/collect";
	}

	public String uri() {
		String literal = this.host.contains(":") ? "[" + this.host + "]" : this.host;
		return "http://" + literal + ":" + port() + "/collect";
	}

	@Override
	public void close() {
		this.server.stop(0);
	}

}
