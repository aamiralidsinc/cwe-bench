import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** Minimal loopback-only HTTP/1.1 stub. Scripts responses per path and records the
 *  Cookie header seen on each incoming request. No external network is used. */
public class StubServer implements Closeable {
    private final ServerSocket server;
    private final Thread acceptor;
    private volatile boolean running = true;
    // path -> ordered list of Cookie header values seen (one entry per request to that path)
    public final Map<String, List<String>> cookiesByPath = new ConcurrentHashMap<>();

    public StubServer() throws IOException {
        server = new ServerSocket();
        server.bind(new InetSocketAddress(InetAddress.getByName("127.0.0.1"), 0));
        acceptor = new Thread(this::loop, "stub-acceptor");
        acceptor.setDaemon(true);
        acceptor.start();
    }

    public int port() { return server.getLocalPort(); }
    public String base() { return "http://127.0.0.1:" + port(); }

    public List<String> cookies(String path) {
        return cookiesByPath.getOrDefault(path, Collections.emptyList());
    }
    public String lastCookie(String path) {
        List<String> l = cookies(path);
        return l.isEmpty() ? null : l.get(l.size() - 1);
    }

    private void loop() {
        while (running) {
            try {
                Socket s = server.accept();
                Thread t = new Thread(() -> handle(s));
                t.setDaemon(true);
                t.start();
            } catch (IOException e) {
                if (running) e.printStackTrace();
            }
        }
    }

    private void handle(Socket s) {
        try (Socket sock = s) {
            sock.setSoTimeout(5000);
            InputStream in = sock.getInputStream();
            OutputStream out = sock.getOutputStream();
            while (running) {
                HttpReq req = readRequest(in);
                if (req == null) return;
                cookiesByPath.computeIfAbsent(req.path, k -> new CopyOnWriteArrayList<>())
                        .add(req.cookie == null ? "<none>" : req.cookie);
                respond(out, req);
                out.flush();
                return; // Connection: close
            }
        } catch (IOException ignored) {
        }
    }

    static class HttpReq {
        String method, path, rawPath;
        String cookie;
        String authorization;
        Map<String,String> headers = new HashMap<>();
        int contentLength;
    }

    private HttpReq readRequest(InputStream in) throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        List<String> lines = new ArrayList<>();
        int prev = -1, c;
        StringBuilder sb = new StringBuilder();
        // read header block
        while (true) {
            c = in.read();
            if (c == -1) return lines.isEmpty() ? null : null;
            if (c == '\n') {
                String ln = sb.toString();
                if (ln.endsWith("\r")) ln = ln.substring(0, ln.length()-1);
                if (ln.isEmpty()) break;
                lines.add(ln);
                sb.setLength(0);
            } else {
                sb.append((char) c);
            }
        }
        if (lines.isEmpty()) return null;
        HttpReq req = new HttpReq();
        String[] parts = lines.get(0).split(" ");
        req.method = parts[0];
        req.rawPath = parts.length > 1 ? parts[1] : "/";
        req.path = req.rawPath;
        int q = req.path.indexOf('?');
        if (q >= 0) req.path = req.path.substring(0, q);
        for (int i = 1; i < lines.size(); i++) {
            String ln = lines.get(i);
            int colon = ln.indexOf(':');
            if (colon < 0) continue;
            String name = ln.substring(0, colon).trim();
            String val = ln.substring(colon + 1).trim();
            req.headers.put(name.toLowerCase(Locale.ROOT), val);
            if (name.equalsIgnoreCase("Cookie")) {
                req.cookie = req.cookie == null ? val : req.cookie + " || " + val;
            } else if (name.equalsIgnoreCase("Authorization")) {
                req.authorization = val;
            } else if (name.equalsIgnoreCase("Content-Length")) {
                req.contentLength = Integer.parseInt(val);
            }
        }
        // drain body
        for (int i = 0; i < req.contentLength; i++) { if (in.read() == -1) break; }
        return req;
    }

    private void respond(OutputStream out, HttpReq req) throws IOException {
        String path = req.path;
        StringBuilder r = new StringBuilder();
        String body = "ok";
        switch (path) {
            case "/seed":
                write(out, 200, Arrays.asList("Set-Cookie: SID=storeval; Path=/"), body);
                return;
            case "/seed-multi":
                write(out, 200, Arrays.asList("Set-Cookie: SID=storeval; Path=/", "Set-Cookie: tracking=xyz; Path=/"), body);
                return;
            case "/redirect":
                write(out, 302, Arrays.asList("Location: /landing"), "");
                return;
            case "/rotate-redirect":
                write(out, 302, Arrays.asList("Location: /landing", "Set-Cookie: SID=rotated; Path=/"), "");
                return;
            case "/auth":
                if (req.authorization == null)
                    write(out, 401, Arrays.asList("WWW-Authenticate: Basic realm=\"r\""), "");
                else
                    write(out, 200, Collections.emptyList(), body);
                return;
            case "/rotate-auth":
                if (req.authorization == null)
                    write(out, 401, Arrays.asList("WWW-Authenticate: Basic realm=\"r\"", "Set-Cookie: SID=rotated; Path=/"), "");
                else
                    write(out, 200, Collections.emptyList(), body);
                return;
            case "/landing":
            default:
                write(out, 200, Collections.emptyList(), body);
                return;
        }
    }

    private void write(OutputStream out, int status, List<String> extra, String body) throws IOException {
        byte[] b = body.getBytes(StandardCharsets.UTF_8);
        StringBuilder sb = new StringBuilder();
        sb.append("HTTP/1.1 ").append(status).append(" S\r\n");
        sb.append("Content-Length: ").append(b.length).append("\r\n");
        sb.append("Connection: close\r\n");
        for (String e : extra) sb.append(e).append("\r\n");
        sb.append("\r\n");
        out.write(sb.toString().getBytes(StandardCharsets.UTF_8));
        out.write(b);
    }

    @Override public void close() {
        running = false;
        try { server.close(); } catch (IOException ignored) {}
    }
}
