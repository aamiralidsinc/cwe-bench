package harness;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import jakarta.servlet.ServletConfig;
import jakarta.servlet.ServletOutputStream;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;
import java.util.concurrent.Executors;

/**
 * Drives the admin console's download servlet through its real doGet entry point with a
 * servlet-container-shaped request/response and a pair of loopback admin REST endpoints.
 * Nothing here is product code: the servlet, its content sources and their REST helpers are
 * compiled from the workspace.
 */
public final class Harness {

    public static final String REST_TOKEN = "__rTkn__";
    public static final String TOKEN_VALUE = "admin-rest-token-29001";
    public static final byte[] ZIP_BYTES = "PK\u0003\u0004payara-client-stub-payload".getBytes(StandardCharsets.ISO_8859_1);
    public static final String LOG_BODY = "server log line one\nserver log line two\n";
    public static final String[] SOURCES = {
        "org.glassfish.admingui.common.servlet.ClientStubsContentSource",
        "org.glassfish.admingui.common.servlet.LogFilesContentSource",
        "org.glassfish.admingui.common.servlet.LogViewerContentSource"
    };

    static {
        // The console's JSF handlers initialise the shared REST client before a download link can
        // be used; emulate that precondition.
        try {
            org.glassfish.admingui.common.util.RestUtil.getJerseyClient();
        } catch (Throwable ignored) {
            // the helpers still report their own failures
        }
    }

    private Harness() {}

    // ---------------------------------------------------------------- request/response

    public static final class Req {
        public final Map<String, String> params = new LinkedHashMap<>();
        public final Map<String, String> headers = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        public final Map<String, Object> session = new LinkedHashMap<>();
        public final Map<String, Object> attrs = new LinkedHashMap<>();
        public String method = "GET";

        public Req(String contentSourceId) {
            params.put("contentSourceId", contentSourceId);
            session.put(REST_TOKEN, TOKEN_VALUE);
        }
        public Req param(String k, String v) { params.put(k, v); return this; }
        public Req header(String k, String v) { headers.put(k, v); return this; }
        public Req session(String k, Object v) { session.put(k, v); return this; }
        public Req copy() {
            Req c = new Req(params.getOrDefault("contentSourceId", "LogFiles"));
            c.params.clear();
            c.params.putAll(params);
            c.headers.putAll(headers);
            c.session.putAll(session);
            c.attrs.putAll(attrs);
            c.method = method;
            return c;
        }
    }

    public static final class Result {
        public int status = 200;
        public boolean sendError;
        public final Map<String, String> headers = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        public byte[] body = new byte[0];
        public Throwable thrown;
        public Path staging;
        public String stagingValue;
        public String responseHeader(String name) { return headers.get(name); }
        public String bodyText() { return new String(body, StandardCharsets.UTF_8); }
        public boolean clientError() { return status >= 400 && status <= 499; }
        public boolean serverError() { return status >= 500; }
    }

    public static Result dispatch(Req r) {
        Result out = new Result();
        Path staging;
        String oldTmp = System.getProperty("java.io.tmpdir");
        try {
            staging = Files.createTempDirectory("payara-stage-");
            out.staging = staging;
            out.stagingValue = staging.toAbsolutePath().toString();
            System.setProperty("java.io.tmpdir", out.stagingValue);

            ByteArrayOutputStream body = new ByteArrayOutputStream();
            ServletOutputStream sos = new ServletOutputStream() {
                @Override public void write(int b) { body.write(b); }
                @Override public void write(byte[] b, int off, int len) { body.write(b, off, len); }
                @Override public boolean isReady() { return true; }
                @Override public void setWriteListener(jakarta.servlet.WriteListener w) {}
            };

            HttpSession session = (HttpSession) Proxy.newProxyInstance(
                Harness.class.getClassLoader(), new Class<?>[]{HttpSession.class},
                new SessionHandler(r.session));
            HttpServletRequest request = (HttpServletRequest) Proxy.newProxyInstance(
                Harness.class.getClassLoader(), new Class<?>[]{HttpServletRequest.class},
                new RequestHandler(r, session));
            HttpServletResponse response = (HttpServletResponse) Proxy.newProxyInstance(
                Harness.class.getClassLoader(), new Class<?>[]{HttpServletResponse.class},
                new ResponseHandler(out, sos));
            ServletConfig config = (ServletConfig) Proxy.newProxyInstance(
                Harness.class.getClassLoader(), new Class<?>[]{ServletConfig.class},
                new ConfigHandler());

            org.glassfish.admingui.common.servlet.DownloadServlet servlet =
                new org.glassfish.admingui.common.servlet.DownloadServlet();
            servlet.init(config);
            try {
                if ("POST".equalsIgnoreCase(r.method)) {
                    servlet.doPost(request, response);
                } else {
                    servlet.doGet(request, response);
                }
            } catch (Throwable t) {
                out.thrown = t;
                out.status = 500;
            }
            out.body = body.toByteArray();
        } catch (Throwable t) {
            out.thrown = t;
            out.status = 500;
        } finally {
            if (oldTmp == null) System.clearProperty("java.io.tmpdir");
            else System.setProperty("java.io.tmpdir", oldTmp);
        }
        return out;
    }

    private static Object zero(Class<?> c) {
        if (!c.isPrimitive()) return null;
        if (c == boolean.class) return false;
        if (c == char.class) return (char) 0;
        if (c == byte.class) return (byte) 0;
        if (c == short.class) return (short) 0;
        if (c == int.class) return 0;
        if (c == long.class) return 0L;
        if (c == float.class) return 0f;
        return 0d;
    }

    private static final class SessionHandler implements InvocationHandler {
        private final Map<String, Object> attrs;
        SessionHandler(Map<String, Object> attrs) { this.attrs = attrs; }
        @Override public Object invoke(Object p, Method m, Object[] a) {
            switch (m.getName()) {
                case "getAttribute": return attrs.get(a[0]);
                case "setAttribute": attrs.put((String) a[0], a[1]); return null;
                case "removeAttribute": attrs.remove(a[0]); return null;
                case "getAttributeNames": return Collections.enumeration(new ArrayList<>(attrs.keySet()));
                case "getValue": return attrs.get(a[0]);
                case "putValue": attrs.put((String) a[0], a[1]); return null;
                case "removeValue": attrs.remove(a[0]); return null;
                case "getValueNames": return attrs.keySet().toArray(new String[0]);
                case "getId": return "session-29001";
                case "getCreationTime": return 1L;
                case "getLastAccessedTime": return 2L;
                case "getMaxInactiveInterval": return 1800;
                case "setMaxInactiveInterval": return null;
                case "invalidate": attrs.clear(); return null;
                case "isNew": return false;
                case "getServletContext": return null;
                case "getSessionContext": return null;
                case "toString": return "MockHttpSession";
                case "hashCode": return System.identityHashCode(p);
                case "equals": return p == a[0];
                default: return zero(m.getReturnType());
            }
        }
    }

    private static final class RequestHandler implements InvocationHandler {
        private final Req r;
        private final HttpSession session;
        RequestHandler(Req r, HttpSession session) { this.r = r; this.session = session; }
        @Override public Object invoke(Object p, Method m, Object[] a) {
            switch (m.getName()) {
                case "getParameter": return r.params.get(a[0]);
                case "getParameterValues": {
                    String v = r.params.get(a[0]);
                    return v == null ? null : new String[]{v};
                }
                case "getParameterMap": {
                    Map<String, String[]> map = new LinkedHashMap<>();
                    for (Map.Entry<String, String> e : r.params.entrySet()) map.put(e.getKey(), new String[]{e.getValue()});
                    return map;
                }
                case "getHeader": return r.headers.get(a[0]);
                case "getHeaders": {
                    String v = r.headers.get(a[0]);
                    return v == null ? Collections.emptyList() : Collections.singletonList(v);
                }
                case "getHeaderNames": return Collections.enumeration(new ArrayList<>(r.headers.keySet()));
                case "getSession": return session;
                case "getMethod": return r.method;
                case "getProtocol": return "HTTP/1.1";
                case "getScheme": return "http";
                case "isSecure": return false;
                case "getServerName": return "console.example";
                case "getServerPort": return 4848;
                case "getContextPath": return "";
                case "getServletPath": return "/download/probe";
                case "getRequestURI": return "/download/probe";
                case "getRequestURL": return new StringBuffer("http://console.example:4848/download/probe");
                case "getQueryString": return "";
                case "getRemoteAddr": return "127.0.0.1";
                case "getRemoteHost": return "127.0.0.1";
                case "getLocale": return Locale.ENGLISH;
                case "getLocales": return Collections.enumeration(Collections.singletonList(Locale.ENGLISH));
                case "getCharacterEncoding": return "UTF-8";
                case "getContentType": return null;
                case "getContentLength": return -1;
                case "getContentLengthLong": return -1L;
                case "getInputStream": return new ByteArrayInputStream(new byte[0]);
                case "getReader": return new java.io.BufferedReader(new java.io.StringReader(""));
                case "getCookies": return null;
                case "getAttribute": return r.attrs.get(a[0]);
                case "setAttribute": r.attrs.put((String) a[0], a[1]); return null;
                case "removeAttribute": r.attrs.remove(a[0]); return null;
                case "getAttributeNames": return Collections.enumeration(new ArrayList<>(r.attrs.keySet()));
                case "isAsyncStarted": return false;
                case "toString": return "MockHttpServletRequest";
                case "hashCode": return System.identityHashCode(p);
                case "equals": return p == a[0];
                default: {
                    // DownloadServlet stores the per-request context under a request attribute.
                    if ("getAttributeNames".equals(m.getName())) return Collections.emptyEnumeration();
                    return zero(m.getReturnType());
                }
            }
        }
    }

    private static final class ResponseHandler implements InvocationHandler {
        private final Result out;
        private final ServletOutputStream sos;
        ResponseHandler(Result out, ServletOutputStream sos) { this.out = out; this.sos = sos; }
        @Override public Object invoke(Object p, Method m, Object[] a) {
            switch (m.getName()) {
                case "setHeader": out.headers.put((String) a[0], String.valueOf(a[1])); return null;
                case "addHeader": out.headers.putIfAbsent((String) a[0], String.valueOf(a[1])); return null;
                case "setDateHeader": out.headers.put((String) a[0], String.valueOf(a[1])); return null;
                case "addDateHeader": out.headers.putIfAbsent((String) a[0], String.valueOf(a[1])); return null;
                case "setIntHeader": out.headers.put((String) a[0], String.valueOf(a[1])); return null;
                case "addIntHeader": out.headers.putIfAbsent((String) a[0], String.valueOf(a[1])); return null;
                case "getHeader": return out.headers.get(a[0]);
                case "containsHeader": return out.headers.containsKey(a[0]);
                case "getHeaders": return Collections.singletonList(out.headers.get(a[0]));
                case "getHeaderNames": return Collections.enumeration(new ArrayList<>(out.headers.keySet()));
                case "setContentType": out.headers.put("Content-Type", String.valueOf(a[0])); return null;
                case "getContentType": return out.headers.get("Content-Type");
                case "setStatus": out.status = (Integer) a[0]; return null;
                case "getStatus": return out.status;
                case "sendError": out.status = (Integer) a[0]; out.sendError = true; return null;
                case "sendRedirect": out.status = 302; return null;
                case "getOutputStream": return sos;
                case "getWriter": return new java.io.PrintWriter(new java.io.OutputStreamWriter(sos, StandardCharsets.UTF_8));
                case "isCommitted": return false;
                case "flushBuffer": try { sos.flush(); } catch (IOException ignored) {} return null;
                case "reset": return null;
                case "resetBuffer": return null;
                case "setCharacterEncoding": return null;
                case "getCharacterEncoding": return "UTF-8";
                case "setContentLength": return null;
                case "setContentLengthLong": return null;
                case "setBufferSize": return null;
                case "getBufferSize": return 0;
                case "getLocale": return Locale.ENGLISH;
                case "setLocale": return null;
                case "toString": return "MockHttpServletResponse";
                case "hashCode": return System.identityHashCode(p);
                case "equals": return p == a[0];
                default: return zero(m.getReturnType());
            }
        }
    }

    private static final class ConfigHandler implements InvocationHandler {
        @Override public Object invoke(Object p, Method m, Object[] a) {
            switch (m.getName()) {
                case "getInitParameter":
                    if ("ContentSources".equals(a[0])) return String.join(",", SOURCES);
                    if ("contentSourceId".equals(a[0])) return "LBConfig";
                    return null;
                case "getInitParameterNames": {
                    List<String> names = new ArrayList<>();
                    names.add("ContentSources");
                    names.add("contentSourceId");
                    return Collections.enumeration(names);
                }
                case "getServletName": return "DownloadServlet";
                case "toString": return "MockServletConfig";
                case "hashCode": return System.identityHashCode(p);
                case "equals": return p == a[0];
                default: return zero(m.getReturnType());
            }
        }
    }

    // ---------------------------------------------------------------- loopback admin REST endpoint

    public static final class Rec {
        public final String method;
        public final String rawPath;
        public final String rawQuery;
        public final String body;
        public final Map<String, List<String>> headers;
        Rec(String method, String rawPath, String rawQuery, String body, Map<String, List<String>> headers) {
            this.method = method; this.rawPath = rawPath; this.rawQuery = rawQuery;
            this.body = body; this.headers = headers;
        }
        public String header(String name) {
            for (Map.Entry<String, List<String>> e : headers.entrySet()) {
                if (e.getKey().equalsIgnoreCase(name) && !e.getValue().isEmpty()) return e.getValue().get(0);
            }
            return null;
        }
        public boolean carriesToken(String token) {
            String c = header("Cookie");
            return c != null && c.contains("gfresttoken=" + token);
        }
        public List<String> queryValues(String name) {
            List<String> vs = new ArrayList<>();
            if (rawQuery == null) return vs;
            for (String part : rawQuery.split("&")) {
                int i = part.indexOf('=');
                String k = i < 0 ? part : part.substring(0, i);
                if (k.equals(name)) vs.add(i < 0 ? "" : URLDecoder.decode(part.substring(i + 1), StandardCharsets.UTF_8));
            }
            return vs;
        }
        public String query(String name) {
            List<String> v = queryValues(name);
            return v.isEmpty() ? null : v.get(0);
        }
        public Map<String, String> form() {
            Map<String, String> out = new LinkedHashMap<>();
            if (body == null) return out;
            for (String part : body.split("&")) {
                if (part.isEmpty()) continue;
                int i = part.indexOf('=');
                String k = i < 0 ? part : part.substring(0, i);
                String v = i < 0 ? "" : part.substring(i + 1);
                out.put(URLDecoder.decode(k, StandardCharsets.UTF_8), URLDecoder.decode(v, StandardCharsets.UTF_8));
            }
            return out;
        }
    }

    public static final class Sink implements AutoCloseable {
        private final HttpServer server;
        private final java.util.concurrent.ExecutorService pool;
        public final List<Rec> records = Collections.synchronizedList(new ArrayList<>());
        public final List<String> writeErrors = Collections.synchronizedList(new ArrayList<>());
        public final String root;      // http://127.0.0.1:<port>
        public final String adminBase; // http://127.0.0.1:<port>/management/domain
        public Sink() throws IOException {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            int port = server.getAddress().getPort();
            root = "http://127.0.0.1:" + port;
            adminBase = root + "/management/domain";
            server.createContext("/", this::handle);
            pool = Executors.newFixedThreadPool(2, r -> {
                Thread t = new Thread(r, "sink-" + port + "-" + UUID.randomUUID());
                t.setDaemon(true);
                return t;
            });
            server.setExecutor(pool);
            server.start();
        }
        private void handle(HttpExchange ex) throws IOException {
            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            URI uri = ex.getRequestURI();
            Rec rec = new Rec(ex.getRequestMethod(), uri.getRawPath(), uri.getRawQuery(), body, ex.getRequestHeaders());
            records.add(rec);
            String path = uri.getRawPath() == null ? "" : uri.getRawPath();
            try {
                if (path.endsWith("/collect-log-files")) {
                    String id = rec.form().get("id");
                    if (id != null && !write(id)) { respond(ex, 500, "application/json", "{\"exit_code\":\"FAILURE\"}"); return; }
                    respond(ex, 200, "application/json", "{\"exit_code\":\"SUCCESS\"}");
                } else if (path.endsWith("/get-client-stubs")) {
                    String localDir = rec.query("localDir");
                    if (localDir != null && !write(localDir)) { respond(ex, 500, "application/json", "{\"exit_code\":\"FAILURE\"}"); return; }
                    respond(ex, 200, "application/json", "{\"exit_code\":\"SUCCESS\"}");
                } else if (path.endsWith("/view-log/") || path.contains("/view-log")) {
                    ex.getResponseHeaders().add("Content-type", "text/plain");
                    ex.getResponseHeaders().add("X-Text-Append-Next", "next-1");
                    respond(ex, 200, "text/plain", LOG_BODY);
                } else {
                    respond(ex, 404, "application/json", "{\"exit_code\":\"FAILURE\"}");
                }
            } catch (IOException e) {
                writeErrors.add(e.toString());
                try { respond(ex, 500, "application/json", "{\"exit_code\":\"FAILURE\"}"); } catch (IOException ignored) {}
            }
        }
        private boolean write(String target) {
            try {
                Path p = Paths.get(target).toAbsolutePath();
                Path parent = p.getParent();
                if (parent != null) {
                    Path cur = parent.getRoot();
                    if (cur == null) cur = Paths.get("").toAbsolutePath();
                    for (Path part : parent) {
                        String name = part.toString();
                        if (name.isEmpty() || name.equals(".")) continue;
                        if (name.equals("..")) { if (cur.getParent() != null) cur = cur.getParent(); continue; }
                        cur = cur.resolve(name);
                        if (!Files.exists(cur)) Files.createDirectory(cur);
                    }
                }
                Files.write(p, ZIP_BYTES);
                return true;
            } catch (Exception e) {
                writeErrors.add(target + ": " + e);
                return false;
            }
        }
        private static void respond(HttpExchange ex, int code, String type, String body) throws IOException {
            byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
            ex.getResponseHeaders().set("Content-type", type);
            ex.sendResponseHeaders(code, bytes.length);
            ex.getResponseBody().write(bytes);
            ex.close();
        }
        public boolean sawPath(String suffix) {
            synchronized (records) {
                for (Rec r : records) if (r.rawPath != null && r.rawPath.endsWith(suffix)) return true;
            }
            return false;
        }
        public List<Rec> all() { synchronized (records) { return new ArrayList<>(records); } }
        public Rec first(String suffix) {
            synchronized (records) {
                for (Rec r : records) if (r.rawPath != null && r.rawPath.endsWith(suffix)) return r;
            }
            return null;
        }
        @Override public void close() { server.stop(0); pool.shutdownNow(); }
    }

    public static boolean inside(Path dir, String value) {
        try {
            Path p = Paths.get(value).toAbsolutePath().normalize();
            Path d = dir.toAbsolutePath().normalize();
            return p.getParent() != null && p.getParent().equals(d);
        } catch (Exception e) {
            return false;
        }
    }

    public static String unique(String stem) { return stem + "-" + UUID.randomUUID().toString().substring(0, 8); }
}
