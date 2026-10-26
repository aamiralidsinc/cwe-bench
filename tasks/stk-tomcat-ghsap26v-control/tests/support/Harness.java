package htests;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.net.HttpURLConnection;
import java.net.ServerSocket;
import java.net.URL;
import java.util.LinkedHashMap;
import java.util.Map;

import javax.servlet.ServletContainerInitializer;

import org.apache.catalina.Context;
import org.apache.catalina.core.StandardContext;
import org.apache.catalina.startup.Tomcat;
import org.apache.tomcat.util.scan.StandardJarScanner;

/**
 * Small in-process HTTP client around a real Tomcat instance. Every test deploys its own
 * web application (or embedded context) and drives it over loopback HTTP.
 */
public class Harness {

    public static final String MARKER = "MARKER-REACHED";

    public static class Resp {
        public int code;
        public String body = "";
        public String cookie;
        public String location;

        public boolean reached() {
            return body != null && body.indexOf(MARKER) >= 0;
        }

        public boolean clientError() {
            return code >= 400 && code < 500;
        }

        public String toString() {
            return "code=" + code + " reached=" + reached() + " location=" + location;
        }
    }

    private final File base;
    private final Tomcat tomcat;
    private final int port;
    private boolean started;

    public Harness() throws IOException {
        base = new File(System.getProperty("java.io.tmpdir"), "htests-" + System.nanoTime());
        if (!base.mkdirs()) {
            throw new IOException("cannot create " + base);
        }
        tomcat = new Tomcat();
        tomcat.setBaseDir(base.getAbsolutePath());
        port = freePort();
        tomcat.setPort(port);
        tomcat.getConnector();
    }

    private static int freePort() throws IOException {
        ServerSocket s = new ServerSocket(0);
        int p = s.getLocalPort();
        s.close();
        return p;
    }

    /** Deploy a web application with the given WEB-INF/web.xml and optional extra files. */
    public Context webapp(String webXml, Map<String, String> files) throws IOException {
        File app = new File(base, "app-" + System.nanoTime());
        if (!app.mkdirs()) throw new IOException("cannot create " + app);
        if (webXml != null) write(new File(app, "WEB-INF/web.xml"), webXml);
        if (files != null) {
            for (Map.Entry<String, String> e : files.entrySet()) {
                write(new File(app, e.getKey()), e.getValue());
            }
        }
        Context ctx = tomcat.addWebapp(null, "", app.getAbsolutePath());
        noClasspathScan(ctx);
        return ctx;
    }

    /** Deploy an embedded context (no web.xml processing) rooted at an empty directory. */
    public Context embedded() throws IOException {
        File doc = new File(base, "doc-" + System.nanoTime());
        if (!doc.mkdirs()) throw new IOException("cannot create " + doc);
        return tomcat.addContext("", doc.getAbsolutePath());
    }

    public void initializer(Context ctx, ServletContainerInitializer sci) {
        ((StandardContext) ctx).addServletContainerInitializer(sci, null);
    }

    public void user(String name, String password) {
        tomcat.addUser(name, password);
    }

    public void role(String name, String role) {
        tomcat.addRole(name, role);
    }

    public void start() throws Exception {
        tomcat.start();
        started = true;
    }

    public Resp get(String path) throws IOException {
        return request("GET", path, null, null, null);
    }

    public Resp get(String path, String cookie) throws IOException {
        return request("GET", path, null, cookie, null);
    }

    public Resp getWithCredentials(String path, String user, String password) throws IOException {
        return request("GET", path, "Basic " + base64(user + ":" + password), null, null);
    }

    public Resp post(String path, String cookie, String formBody) throws IOException {
        return request("POST", path, null, cookie, formBody);
    }

    private Resp request(String method, String path, String authorization, String cookie, String formBody)
            throws IOException {
        URL url = new URL("http://127.0.0.1:" + port + path);
        HttpURLConnection c = (HttpURLConnection) url.openConnection();
        c.setInstanceFollowRedirects(false);
        c.setRequestMethod(method);
        c.setConnectTimeout(20000);
        c.setReadTimeout(20000);
        if (authorization != null) c.setRequestProperty("Authorization", authorization);
        if (cookie != null) c.setRequestProperty("Cookie", cookie);
        if (formBody != null) {
            c.setDoOutput(true);
            c.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            OutputStream os = c.getOutputStream();
            os.write(formBody.getBytes("UTF-8"));
            os.close();
        }
        Resp r = new Resp();
        try {
            r.code = c.getResponseCode();
            InputStream is = r.code < 400 ? c.getInputStream() : c.getErrorStream();
            if (is != null) {
                BufferedReader br = new BufferedReader(new InputStreamReader(is, "ISO-8859-1"));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) sb.append(line);
                r.body = sb.toString();
            }
            String sc = c.getHeaderField("Set-Cookie");
            if (sc != null) {
                int semi = sc.indexOf(';');
                r.cookie = semi >= 0 ? sc.substring(0, semi) : sc;
            }
            r.location = c.getHeaderField("Location");
        } finally {
            c.disconnect();
        }
        return r;
    }

    private static void noClasspathScan(Context ctx) {
        StandardJarScanner scanner = new StandardJarScanner();
        scanner.setScanClassPath(false);
        ((StandardContext) ctx).setJarScanner(scanner);
    }

    private static void write(File f, String content) throws IOException {
        File parent = f.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IOException("cannot create " + parent);
        }
        Writer w = new OutputStreamWriter(new FileOutputStream(f), "ISO-8859-1");
        w.write(content);
        w.close();
    }

    public static String base64(String value) {
        final String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        byte[] data;
        try {
            data = value.getBytes("UTF-8");
        } catch (IOException e) {
            data = value.getBytes();
        }
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < data.length; i += 3) {
            int b0 = data[i] & 0xff;
            int b1 = i + 1 < data.length ? data[i + 1] & 0xff : 0;
            int b2 = i + 2 < data.length ? data[i + 2] & 0xff : 0;
            out.append(alphabet.charAt(b0 >> 2));
            out.append(alphabet.charAt(((b0 & 3) << 4) | (b1 >> 4)));
            out.append(i + 1 < data.length ? alphabet.charAt(((b1 & 15) << 2) | (b2 >> 6)) : '=');
            out.append(i + 2 < data.length ? alphabet.charAt(b2 & 63) : '=');
        }
        return out.toString();
    }

    /** XML helper: a small 3.0 deployment descriptor around the supplied body. */
    public static String webXml(String body) {
        return "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n"
             + "<web-app xmlns=\"http://java.sun.com/xml/ns/javaee\" version=\"3.0\">\n"
             + body + "\n</web-app>\n";
    }

    public static Map<String, String> files(String... pairs) {
        Map<String, String> m = new LinkedHashMap<String, String>();
        for (int i = 0; i + 1 < pairs.length; i += 2) m.put(pairs[i], pairs[i + 1]);
        return m;
    }

    public void close() {
        try {
            if (started) {
                tomcat.stop();
                tomcat.destroy();
            }
        } catch (Throwable ignored) {
            // best effort
        } finally {
            delete(base);
        }
    }

    private static void delete(File f) {
        if (f == null || !f.exists()) return;
        File[] kids = f.listFiles();
        if (kids != null) for (int i = 0; i < kids.length; i++) delete(kids[i]);
        f.delete();
    }
}
