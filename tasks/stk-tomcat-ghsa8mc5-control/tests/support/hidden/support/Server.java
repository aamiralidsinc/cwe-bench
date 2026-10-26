/*
 * Test support: starts a real embedded Tomcat with TLS connectors that serve several virtual
 * hosts under different TLS configurations, and drives real HTTP/1.1 and HTTP/2 requests at it.
 * Nothing here is product code; the assertions live in the security/functional tests.
 */
package hidden.support;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyStore;
import java.security.cert.X509Certificate;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

import javax.net.ssl.KeyManager;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SNIHostName;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.apache.catalina.Context;
import org.apache.catalina.Host;
import org.apache.catalina.connector.Connector;
import org.apache.catalina.core.StandardHost;
import org.apache.catalina.startup.Tomcat;
import org.apache.coyote.http2.Http2Protocol;
import org.apache.tomcat.util.net.SSLHostConfig;
import org.apache.tomcat.util.net.SSLHostConfigCertificate;

/**
 * One embedded server per test class. Hosts:
 *   weak.example.com      default host, served by the default TLS configuration
 *   strict.example.com    virtual host with its own TLS configuration that requires a client certificate
 *   internal.example.com  a host used behind a connector that fixes the served name
 *   a.example.com / b.example.com  two hosts that share a wildcard TLS configuration
 */
public final class Server {

    public static final String WEAK = "weak.example.com";
    public static final String STRICT = "strict.example.com";
    public static final String INTERNAL = "internal.example.com";
    public static final String A = "a.example.com";
    public static final String B = "b.example.com";

    private static final Map<String, AtomicInteger> HITS = new ConcurrentHashMap<>();
    private static final String ASSETS = System.getProperty("tests.assets", "/tests/assets");

    private final Tomcat tomcat;
    private final Path baseDir;
    private final int nioPort;
    private final int nio2Port;
    private final int proxyStrictPort;
    private final int proxyInternalPort;
    private final int wildPort;
    private final int h2Port;

    public static Server start() throws Exception {
        return new Server();
    }

    private Server() throws Exception {
        baseDir = Files.createTempDirectory("sni-server");
        tomcat = new Tomcat();
        tomcat.setBaseDir(baseDir.toString());
        tomcat.getEngine().setDefaultHost(WEAK);
        addHost(WEAK, "WEAK", true);
        addHost(STRICT, "STRICT", false);
        addHost(INTERNAL, "INTERNAL", false);
        addHost(A, "A", false);
        addHost(B, "B", false);

        Connector nio = connector("org.apache.coyote.http11.Http11NioProtocol", null, false, false);
        Connector nio2 = connector("org.apache.coyote.http11.Http11Nio2Protocol", null, false, false);
        Connector proxyStrict = connector("org.apache.coyote.http11.Http11NioProtocol", STRICT, false, false);
        Connector proxyInternal = connector("org.apache.coyote.http11.Http11NioProtocol", INTERNAL, false, false);
        Connector wild = connector("org.apache.coyote.http11.Http11NioProtocol", null, true, false);
        Connector h2 = connector("org.apache.coyote.http11.Http11NioProtocol", null, true, true);

        tomcat.start();
        nioPort = nio.getLocalPort();
        nio2Port = nio2.getLocalPort();
        proxyStrictPort = proxyStrict.getLocalPort();
        proxyInternalPort = proxyInternal.getLocalPort();
        wildPort = wild.getLocalPort();
        h2Port = h2.getLocalPort();
    }

    public void stop() {
        try {
            tomcat.stop();
        } catch (Exception ignored) {
            // best effort in a test teardown
        }
        try {
            tomcat.destroy();
        } catch (Exception ignored) {
            // best effort in a test teardown
        }
        try {
            delete(baseDir.toFile());
        } catch (Exception ignored) {
            // best effort in a test teardown
        }
    }

    private void addHost(String name, String tag, boolean isDefault) throws IOException {
        Host host;
        if (isDefault) {
            host = tomcat.getHost();
            host.setName(name);
        } else {
            host = new StandardHost();
            host.setName(name);
            tomcat.getEngine().addChild(host);
        }
        host.setAppBase(baseDir.toString());
        host.setAutoDeploy(false);
        host.setDeployOnStartup(false);
        File docBase = baseDir.resolve("docbase-" + name).toFile();
        Files.createDirectories(docBase.toPath());
        Context context = tomcat.addContext(host, "", docBase.getAbsolutePath());
        Tomcat.addServlet(context, "s", new MarkerServlet(tag));
        context.addServletMappingDecoded("/", "s");
    }

    private static SSLHostConfig sslConfig(String hostName, boolean clientCertificateRequired) {
        SSLHostConfig config = new SSLHostConfig();
        if (hostName != null) {
            config.setHostName(hostName);
        }
        SSLHostConfigCertificate certificate = new SSLHostConfigCertificate(config,
                SSLHostConfigCertificate.Type.UNDEFINED);
        config.addCertificate(certificate);
        certificate.setCertificateKeystoreFile(new File(ASSETS, "localhost-rsa.jks").getAbsolutePath());
        certificate.setCertificateKeystorePassword("changeit");
        config.setTruststoreFile(new File(ASSETS, "ca.jks").getAbsolutePath());
        config.setTruststorePassword("changeit");
        config.setCertificateVerification(clientCertificateRequired ? "required" : "none");
        return config;
    }

    private Connector connector(String protocol, String proxyName, boolean wildcard, boolean http2) {
        Connector connector = new Connector(protocol);
        connector.setPort(0);
        connector.setSecure(true);
        connector.setScheme("https");
        connector.setProperty("SSLEnabled", "true");
        connector.addSslHostConfig(sslConfig(null, false));
        connector.addSslHostConfig(sslConfig(STRICT, true));
        if (wildcard) {
            connector.addSslHostConfig(sslConfig("*.example.com", false));
        }
        if (proxyName != null) {
            connector.setProxyName(proxyName);
        }
        if (http2) {
            connector.addUpgradeProtocol(new Http2Protocol());
        }
        tomcat.getService().addConnector(connector);
        return connector;
    }

    // ---------------------------------------------------------------- HTTP/1.1

    public HttpResult get(int port, String tlsName, String requestHost, boolean clientCertificate)
            throws Exception {
        return get(port, tlsName, requestHost, clientCertificate, 10000);
    }

    public HttpResult get(int port, String tlsName, String requestHost, boolean clientCertificate, int timeoutMs)
            throws Exception {
        resetHits();
        HttpResult result = new HttpResult();
        try (SSLSocket socket = socket(port, tlsName, clientCertificate, null)) {
            socket.setSoTimeout(timeoutMs);
            socket.startHandshake();
            OutputStream out = socket.getOutputStream();
            String request = "GET / HTTP/1.1\r\nHost: " + requestHost + "\r\nConnection: close\r\n\r\n";
            out.write(request.getBytes(StandardCharsets.ISO_8859_1));
            out.flush();
            String response = readAll(socket.getInputStream());
            result.raw = response;
            int firstLineEnd = response.indexOf("\r\n");
            String statusLine = firstLineEnd < 0 ? response : response.substring(0, firstLineEnd);
            result.statusLine = statusLine;
            result.status = parseStatus(statusLine);
            result.body = response;
        } catch (Exception e) {
            result.exception = e.getClass().getSimpleName() + ": " + e.getMessage();
        }
        result.hits = totalHits();
        return result;
    }

    private static int parseStatus(String statusLine) {
        // "HTTP/1.1 400 Bad Request"
        String[] parts = statusLine.split(" ");
        if (parts.length < 2) {
            return -1;
        }
        try {
            return Integer.parseInt(parts[1]);
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    // ---------------------------------------------------------------- HTTP/2

    public H2Result h2(String tlsName, String authority, boolean clientCertificate) throws Exception {
        resetHits();
        H2Result result = new H2Result();
        try (SSLSocket socket = socket(h2Port, tlsName, clientCertificate, new String[] { "h2" })) {
            socket.setSoTimeout(8000);
            socket.startHandshake();
            result.alpn = "h2".equals(socket.getApplicationProtocol());
            if (!result.alpn) {
                result.events = "no h2 ALPN";
                result.hits = totalHits();
                return result;
            }
            OutputStream out = socket.getOutputStream();
            out.write("PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n".getBytes(StandardCharsets.ISO_8859_1));
            out.write(frame(4, 0, 0, new byte[0]));
            out.write(frame(1, 0x5, 1, headersPayload(authority)));
            out.flush();
            readH2(socket.getInputStream(), result);
        } catch (SocketTimeoutException e) {
            result.events = result.events + " timeout";
        } catch (Exception e) {
            result.events = result.events + " " + e.getClass().getSimpleName();
        }
        result.hits = totalHits();
        return result;
    }

    private static void readH2(InputStream in, H2Result result) throws IOException {
        long deadline = System.currentTimeMillis() + 5000;
        byte[] header = new byte[9];
        StringBuilder events = new StringBuilder();
        ByteArrayOutputStream data = new ByteArrayOutputStream();
        while (System.currentTimeMillis() < deadline) {
            if (!readFully(in, header)) {
                events.append("eof ");
                result.eof = true;
                break;
            }
            int length = ((header[0] & 0xff) << 16) | ((header[1] & 0xff) << 8) | (header[2] & 0xff);
            int type = header[3] & 0xff;
            int flags = header[4] & 0xff;
            int stream = ((header[5] & 0x7f) << 24) | ((header[6] & 0xff) << 16) | ((header[7] & 0xff) << 8)
                    | (header[8] & 0xff);
            byte[] payload = new byte[length];
            if (!readFully(in, payload)) {
                events.append("truncated ");
                result.eof = true;
                break;
            }
            events.append("t").append(type).append("s").append(stream).append(' ');
            if (type == 0 && stream == 1) {
                data.write(payload);
                result.sawData = true;
            }
            if (type == 3) { // RST_STREAM
                result.sawReset = true;
                if (payload.length >= 4) {
                    result.errorCode = readInt(payload, 0);
                }
                break;
            }
            if (type == 7) { // GOAWAY
                result.sawGoaway = true;
                if (payload.length >= 8) {
                    result.errorCode = readInt(payload, 4);
                }
                break;
            }
            if (type == 1 && stream == 1) {
                result.sawHeaders = true;
            }
            if (type == 0 && (flags & 0x1) != 0) {
                break;
            }
        }
        result.events = events.toString().trim();
        result.body = data.toString("ISO-8859-1");
    }

    private static int readInt(byte[] b, int off) {
        return ((b[off] & 0xff) << 24) | ((b[off + 1] & 0xff) << 16) | ((b[off + 2] & 0xff) << 8)
                | (b[off + 3] & 0xff);
    }

    private static byte[] frame(int type, int flags, int stream, byte[] payload) {
        byte[] frame = new byte[9 + payload.length];
        frame[0] = (byte) ((payload.length >> 16) & 0xff);
        frame[1] = (byte) ((payload.length >> 8) & 0xff);
        frame[2] = (byte) (payload.length & 0xff);
        frame[3] = (byte) type;
        frame[4] = (byte) flags;
        frame[5] = (byte) ((stream >> 24) & 0x7f);
        frame[6] = (byte) ((stream >> 16) & 0xff);
        frame[7] = (byte) ((stream >> 8) & 0xff);
        frame[8] = (byte) (stream & 0xff);
        System.arraycopy(payload, 0, frame, 9, payload.length);
        return frame;
    }

    private static byte[] headersPayload(String authority) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        out.write(literal(":method", "GET"));
        out.write(literal(":scheme", "https"));
        out.write(literal(":path", "/"));
        if (authority != null) {
            out.write(literal(":authority", authority));
        }
        return out.toByteArray();
    }

    private static byte[] literal(String name, String value) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] nameBytes = name.getBytes(StandardCharsets.ISO_8859_1);
        byte[] valueBytes = value.getBytes(StandardCharsets.ISO_8859_1);
        out.write(0x00);
        out.write(nameBytes.length);
        out.write(nameBytes);
        out.write(valueBytes.length);
        out.write(valueBytes);
        return out.toByteArray();
    }

    // ---------------------------------------------------------------- plumbing

    private static SSLSocket socket(int port, String tlsName, boolean clientCertificate, String[] alpn)
            throws Exception {
        javax.net.ssl.SSLContext context = javax.net.ssl.SSLContext.getInstance("TLS");
        TrustManager[] trust = new TrustManager[] { new X509TrustManager() {
            @Override
            public void checkClientTrusted(X509Certificate[] chain, String authType) {
            }

            @Override
            public void checkServerTrusted(X509Certificate[] chain, String authType) {
            }

            @Override
            public X509Certificate[] getAcceptedIssuers() {
                return new X509Certificate[0];
            }
        } };
        KeyManager[] keys = null;
        if (clientCertificate) {
            KeyStore keyStore = KeyStore.getInstance("JKS");
            try (InputStream in = new FileInputStream(new File(ASSETS, "user1.jks"))) {
                keyStore.load(in, "changeit".toCharArray());
            }
            KeyManagerFactory factory = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
            factory.init(keyStore, "changeit".toCharArray());
            keys = factory.getKeyManagers();
        }
        context.init(keys, trust, null);
        SSLSocket socket = (SSLSocket) context.getSocketFactory().createSocket("127.0.0.1", port);
        SSLParameters parameters = socket.getSSLParameters();
        if (tlsName != null) {
            parameters.setServerNames(Collections.singletonList(new SNIHostName(tlsName)));
        }
        if (alpn != null) {
            parameters.setApplicationProtocols(alpn);
        }
        socket.setSSLParameters(parameters);
        return socket;
    }

    private static String readAll(InputStream in) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        try {
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
        } catch (IOException ignored) {
            // a reset after the response is still a response
        }
        return out.toString("ISO-8859-1");
    }

    private static boolean readFully(InputStream in, byte[] buffer) throws IOException {
        int offset = 0;
        while (offset < buffer.length) {
            int read = in.read(buffer, offset, buffer.length - offset);
            if (read < 0) {
                return false;
            }
            offset += read;
        }
        return true;
    }

    private static void delete(File file) {
        File[] children = file.listFiles();
        if (children != null) {
            for (File child : children) {
                delete(child);
            }
        }
        file.delete();
    }

    public void resetHits() {
        HITS.clear();
    }

    public int hits(String tag) {
        AtomicInteger count = HITS.get(tag);
        return count == null ? 0 : count.get();
    }

    private static int totalHits() {
        int total = 0;
        for (AtomicInteger count : HITS.values()) {
            total += count.get();
        }
        return total;
    }

    public int nioPort() {
        return nioPort;
    }

    public int nio2Port() {
        return nio2Port;
    }

    public int proxyStrictPort() {
        return proxyStrictPort;
    }

    public int proxyInternalPort() {
        return proxyInternalPort;
    }

    public int wildPort() {
        return wildPort;
    }

    public int h2Port() {
        return h2Port;
    }

    public static final class MarkerServlet extends HttpServlet {
        private static final long serialVersionUID = 1L;
        private final String tag;

        MarkerServlet(String tag) {
            this.tag = tag;
        }

        @Override
        protected void doGet(HttpServletRequest request, HttpServletResponse response) throws IOException {
            HITS.computeIfAbsent(tag, key -> new AtomicInteger()).incrementAndGet();
            response.setStatus(200);
            response.setContentType("text/plain");
            response.getWriter().write(tag + "-OK");
        }
    }

    public static final class HttpResult {
        public int status = -1;
        public String statusLine = "";
        public String body = "";
        public String raw = "";
        public String exception;
        public int hits;

        public boolean clientError() {
            return status >= 400 && status < 500;
        }

        @Override
        public String toString() {
            return "status=" + status + " statusLine=" + statusLine + " hits=" + hits
                    + (exception == null ? "" : " exception=" + exception);
        }
    }

    public static final class H2Result {
        public boolean alpn;
        public boolean sawHeaders;
        public boolean sawData;
        public boolean sawReset;
        public boolean sawGoaway;
        public boolean eof;
        public int errorCode;
        public int hits;
        public String body = "";
        public String events = "";

        @Override
        public String toString() {
            return "alpn=" + alpn + " events=[" + events + "] hits=" + hits + " errorCode=" + errorCode
                    + " body=" + body;
        }
    }
}
