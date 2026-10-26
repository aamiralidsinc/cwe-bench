package bench.camel;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import com.sun.net.httpserver.HttpServer;
import org.apache.camel.Exchange;
import org.apache.camel.spi.HeaderFilterStrategy;

/**
 * Test-owned helpers: no product class is used to compute an expectation or a cleanup, so a
 * hardened product cannot make a test crash or change its own expected values.
 */
public final class Harness {

    public static final long WAIT_SECONDS = 15L;

    private Harness() {
    }

    /** A bounded, per-test body: a hung server fails the case instead of hanging the suite. */
    public static void run(long seconds, Body body) throws Exception {
        ExecutorService pool = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "case");
            t.setDaemon(true);
            return t;
        });
        Future<?> future = pool.submit(() -> {
            try {
                body.run();
            } catch (RuntimeException | Error e) {
                throw e;
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
        try {
            future.get(seconds, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            future.cancel(true);
            throw new AssertionError("case timed out after " + seconds + "s");
        } catch (ExecutionException e) {
            Throwable cause = e.getCause();
            if (cause instanceof Error) {
                throw (Error) cause;
            }
            if (cause instanceof Exception) {
                throw (Exception) cause;
            }
            throw new RuntimeException(cause);
        } finally {
            pool.shutdownNow();
        }
    }

    @FunctionalInterface
    public interface Body {
        void run() throws Exception;
    }

    public static int freePort() throws IOException {
        try (ServerSocket socket = new ServerSocket(0)) {
            socket.setReuseAddress(true);
            return socket.getLocalPort();
        }
    }

    /** A caller-supplied header name is present, matched case-insensitively. */
    public static Object header(Map<String, Object> headers, String name) {
        for (Map.Entry<String, Object> entry : headers.entrySet()) {
            if (entry.getKey().equalsIgnoreCase(name)) {
                return entry.getValue();
            }
        }
        return null;
    }

    public interface Response {
        int status();

        boolean ok();
    }

    /**
     * Sends one raw request. Raw sockets are used so a test can put any header name on the wire,
     * including names that the product's own clients would refuse to send.
     */
    public static Response request(
            int port, String method, String path, Map<String, String> headers, String body)
            throws IOException {
        try (Socket socket = new Socket("127.0.0.1", port)) {
            socket.setSoTimeout((int) TimeUnit.SECONDS.toMillis(WAIT_SECONDS));
            StringBuilder request = new StringBuilder();
            request.append(method).append(' ').append(path).append(" HTTP/1.1\r\n");
            request.append("Host: 127.0.0.1:").append(port).append("\r\n");
            if (headers != null) {
                for (Map.Entry<String, String> entry : headers.entrySet()) {
                    request.append(entry.getKey()).append(": ").append(entry.getValue()).append("\r\n");
                }
            }
            if (body != null) {
                byte[] payload = body.getBytes(StandardCharsets.UTF_8);
                request.append("Content-Type: text/plain\r\n");
                request.append("Content-Length: ").append(payload.length).append("\r\n");
                request.append("Connection: close\r\n\r\n");
                OutputStream out = socket.getOutputStream();
                out.write(request.toString().getBytes(StandardCharsets.UTF_8));
                out.write(payload);
                out.flush();
            } else {
                request.append("Connection: close\r\n\r\n");
                OutputStream out = socket.getOutputStream();
                out.write(request.toString().getBytes(StandardCharsets.UTF_8));
                out.flush();
            }
            InputStream in = socket.getInputStream();
            ByteArrayOutputStream raw = new ByteArrayOutputStream();
            byte[] buffer = new byte[4096];
            int read;
            while ((read = in.read(buffer)) != -1) {
                raw.write(buffer, 0, read);
            }
            String text = raw.toString(StandardCharsets.UTF_8);
            int status = 0;
            if (text.startsWith("HTTP/")) {
                String[] parts = text.substring(0, Math.min(text.length(), 40)).split(" ");
                if (parts.length > 1) {
                    try {
                        status = Integer.parseInt(parts[1].trim());
                    } catch (NumberFormatException ignored) {
                        status = 0;
                    }
                }
            }
            final int code = status;
            return new Response() {
                @Override
                public int status() {
                    return code;
                }

                @Override
                public boolean ok() {
                    return code >= 200 && code < 300;
                }
            };
        }
    }

    public static Response get(int port, String path, Map<String, String> headers) throws IOException {
        return request(port, "GET", path, headers, null);
    }

    /** A loopback HTTP peer that records the headers of each request it receives. */
    public static final class Recorder implements AutoCloseable {
        private final HttpServer server;
        public final BlockingQueue<Map<String, String>> requests = new LinkedBlockingQueue<>();

        public Recorder(Map<String, String> responseHeaders) throws IOException {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.createContext("/", exchange -> {
                Map<String, String> received = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
                exchange.getRequestHeaders().forEach((name, values) -> received.put(name, values.toString()));
                received.put(":path", exchange.getRequestURI().toString());
                requests.add(received);
                if (responseHeaders != null) {
                    for (Map.Entry<String, String> entry : responseHeaders.entrySet()) {
                        exchange.getResponseHeaders().add(entry.getKey(), entry.getValue());
                    }
                }
                byte[] payload = "ok".getBytes(StandardCharsets.UTF_8);
                exchange.sendResponseHeaders(200, payload.length);
                exchange.getResponseBody().write(payload);
                exchange.close();
            });
            server.start();
        }

        public int port() {
            return server.getAddress().getPort();
        }

        public Map<String, String> awaitRequest() throws InterruptedException {
            return requests.poll(WAIT_SECONDS, TimeUnit.SECONDS);
        }

        @Override
        public void close() {
            server.stop(0);
        }
    }

    /**
     * A test-owned strategy: it denies a few exact names plus the component's control namespaces.
     * It is the kind of strategy an operator writes, and it is independent of the code under test.
     */
    public static final class DenyStrategy implements HeaderFilterStrategy {
        private final java.util.Set<String> denied = new java.util.HashSet<>();

        public DenyStrategy deny(String name) {
            denied.add(name.toLowerCase());
            return this;
        }

        private boolean blocks(String name) {
            if (name == null) {
                return true;
            }
            String lower = name.toLowerCase();
            if (denied.contains(lower)) {
                return true;
            }
            return lower.startsWith("camel") || lower.startsWith("org.apache.camel.")
                    || lower.startsWith("websocket.");
        }

        @Override
        public boolean applyFilterToCamelHeaders(String name, Object value, Exchange exchange) {
            return blocks(name);
        }

        @Override
        public boolean applyFilterToExternalHeaders(String name, Object value, Exchange exchange) {
            return blocks(name);
        }
    }

    public static Map<String, String> headers(String... pairs) {
        Map<String, String> map = new LinkedHashMap<>();
        for (int i = 0; i + 1 < pairs.length; i += 2) {
            map.put(pairs[i], pairs[i + 1]);
        }
        return map;
    }
}
