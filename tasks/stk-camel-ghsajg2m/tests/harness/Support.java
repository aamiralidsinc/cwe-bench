package org.apache.camel.htests;

import java.io.IOException;

import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import org.apache.camel.CamelContext;
import org.apache.camel.impl.DefaultCamelContext;

/**
 * Shared helpers for the hidden groups. Nothing here touches product internals: it only starts a
 * context, picks a free loopback port and speaks plain HTTP to the routes the tests install.
 */
public final class Support {

    private Support() {
    }

    public static int freePort() throws IOException {
        try (ServerSocket socket = new ServerSocket(0)) {
            socket.setReuseAddress(true);
            return socket.getLocalPort();
        }
    }

    public static CamelContext newContext() {
        CamelContext context = new DefaultCamelContext();
        context.getCamelContextExtension().setName("htests-" + System.nanoTime());
        return context;
    }

    public static HttpResponse<String> get(int port, String path, String... headers) throws Exception {
        HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + path))
                .timeout(Duration.ofSeconds(30))
                .GET();
        for (int i = 0; i + 1 < headers.length; i += 2) {
            builder.header(headers[i], headers[i + 1]);
        }
        return client.send(builder.build(), HttpResponse.BodyHandlers.ofString());
    }

    public static HttpResponse<String> send(int port, String method, String path, String body, String... headers)
            throws Exception {
        HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + path))
                .timeout(Duration.ofSeconds(30))
                .method(method, body == null
                        ? HttpRequest.BodyPublishers.noBody()
                        : HttpRequest.BodyPublishers.ofString(body));
        for (int i = 0; i + 1 < headers.length; i += 2) {
            builder.header(headers[i], headers[i + 1]);
        }
        return client.send(builder.build(), HttpResponse.BodyHandlers.ofString());
    }

    /** A value a client-controlled name must never produce in the message. */
    public static final String MARKER = "INJECTED-9f3a";

    /** The route reports INJECTED-9f3a when a client-supplied name became one of Camel's headers. */
    public static void assertNotInjected(String surface, Object observed) {
        String text = String.valueOf(observed);
        if (text.contains(MARKER)) {
            throw new AssertionError(surface + ": a client-supplied name became one of Camel's own message headers: "
                    + text);
        }
    }

    public static void assertProcessedNormally(String surface, HttpResponse<String> response) {
        int status = response.statusCode();
        if (status < 200 || status >= 300) {
            throw new AssertionError(surface + ": the request was not processed normally (status " + status
                    + ", body " + response.body() + "); dropping a client-supplied name must leave the request "
                    + "otherwise untouched");
        }
        assertNotInjected(surface, response.body());
    }

    public static void close(CamelContext context) {
        if (context == null) {
            return;
        }
        try {
            context.stop();
        } catch (Exception ignored) {
            // a test context that fails to stop must not mask the test result
        }
    }

    public static void awaitPort(int port, long timeoutMillis) throws Exception {
        long deadline = System.currentTimeMillis() + timeoutMillis;
        Exception last = null;
        while (System.currentTimeMillis() < deadline) {
            try (java.net.Socket socket = new java.net.Socket()) {
                socket.connect(new InetSocketAddress("127.0.0.1", port), 500);
                socket.close();
                return;
            } catch (IOException e) {
                last = e;
                Thread.sleep(100);
            }
        }
        throw new IllegalStateException("port " + port + " never started listening", last);
    }
}
