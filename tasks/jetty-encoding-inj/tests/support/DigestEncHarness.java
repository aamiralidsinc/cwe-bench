//
// Shared, self-contained test harness for the authentication-encoding tests.
// It stands up a real in-process server (no sockets, no network) using a
// LocalConnector, a path-mapped security handler and a hash-backed login
// service seeded programmatically, then drives it with raw HTTP request
// strings. All expected hashes are computed here in the test, never by
// importing a product helper, so hardening the product cannot crash a test.
//
package org.eclipse.jetty.security;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.jetty.http.HttpHeader;
import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.io.Content;
import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.LocalConnector;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.server.handler.ContextHandler;
import org.eclipse.jetty.session.SessionHandler;
import org.eclipse.jetty.util.Callback;
import org.eclipse.jetty.util.security.Credential;

public class DigestEncHarness implements AutoCloseable
{
    public static final String REALM = "TestRealm";
    public static final String CTX = "/ctx";
    public static final String PATH = "/ctx/prot/resource";

    private final Server server;
    private final LocalConnector connector;
    private final UserStore store = new UserStore();

    public DigestEncHarness(Authenticator authenticator) throws Exception
    {
        this(authenticator, null);
    }

    public DigestEncHarness(Authenticator authenticator, Charset basicCharset) throws Exception
    {
        server = new Server();
        connector = new LocalConnector(server);
        connector.setIdleTimeout(300000);
        server.addConnector(connector);

        HashLoginService loginService = new HashLoginService(REALM);
        loginService.setUserStore(store);

        ContextHandler context = new ContextHandler();
        context.setContextPath(CTX);
        SessionHandler session = new SessionHandler();
        context.setHandler(session);

        SecurityHandler.PathMapped security = new SecurityHandler.PathMapped();
        security.setLoginService(loginService);
        if (authenticator instanceof BasicAuthenticator && basicCharset != null)
            ((BasicAuthenticator)authenticator).setCharset(basicCharset);
        security.setAuthenticator(authenticator);
        security.put("/prot/*", Constraint.ANY_USER);
        session.setHandler(security);

        security.setHandler(new Handler.Abstract()
        {
            @Override
            public boolean handle(Request request, Response response, Callback callback)
            {
                String body = "NOAUTH";
                AuthenticationState as = AuthenticationState.getAuthenticationState(request);
                if (as instanceof AuthenticationState.Succeeded s)
                    body = "AUTHED:" + s.getUserIdentity().getUserPrincipal().getName();
                response.getHeaders().add(HttpHeader.CONTENT_TYPE, "text/plain");
                Content.Sink.write(response, true, body, callback);
                return true;
            }
        });

        server.setHandler(context);
        server.start();
    }

    /** Seed a user. {@code credential} is any form Credential.getCredential understands
     *  (a plain password, or a "MD5:"/"SHA1:" prefixed stored hash). */
    public void addUser(String name, String credential)
    {
        store.addUser(name, Credential.getCredential(credential), new String[]{"user"});
    }

    @Override
    public void close() throws Exception
    {
        if (server.isRunning())
        {
            server.stop();
            server.join();
        }
    }

    // ---- raw request driving ------------------------------------------------

    public HttpTester.Response raw(String rawRequest) throws Exception
    {
        return HttpTester.parseResponse(connector.getResponse(rawRequest));
    }

    public HttpTester.Response get(String path) throws Exception
    {
        return raw("GET " + path + " HTTP/1.0\r\nHost: local\r\n\r\n");
    }

    public HttpTester.Response getWithAuth(String path, String authorization) throws Exception
    {
        return raw("GET " + path + " HTTP/1.0\r\nHost: local\r\nAuthorization: " + authorization + "\r\n\r\n");
    }

    // ---- Basic auth ---------------------------------------------------------

    /** A Basic header whose decoded password bytes are {@code password} encoded with {@code charset}. */
    public static String basicHeader(String user, String password, Charset charset)
    {
        byte[] bytes = (user + ":" + password).getBytes(charset);
        return "Basic " + Base64.getEncoder().encodeToString(bytes);
    }

    // ---- Digest auth --------------------------------------------------------

    /** Perform a full Digest exchange: GET to obtain the challenge, then resend with a
     *  computed response. {@code password} is hashed into H(A1) using {@code pwCharset}
     *  and {@code algorithm} ("MD5" or "SHA-256"). Returns the second response. */
    public HttpTester.Response digest(String user, String password, String algorithm, Charset pwCharset) throws Exception
    {
        HttpTester.Response challenge = get(PATH);
        String wwwAuth = challenge.get(HttpHeader.WWW_AUTHENTICATE);
        String nonce = param(wwwAuth, "nonce");
        String qop = "auth";
        String nc = "00000001";
        String cnonce = "clientnonce";
        String uri = PATH;
        String method = "GET";

        String ha1 = hashHex(algorithm, (user + ":" + REALM + ":" + password).getBytes(pwCharset));
        String ha2 = hashHex(algorithm, (method + ":" + uri).getBytes(StandardCharsets.ISO_8859_1));
        String responseHash = hashHex(algorithm,
            (ha1 + ":" + nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + ha2).getBytes(StandardCharsets.ISO_8859_1));

        String header = "Digest username=\"" + user + "\", realm=\"" + REALM + "\", nonce=\"" + nonce +
            "\", uri=\"" + uri + "\", qop=" + qop + ", nc=" + nc + ", cnonce=\"" + cnonce +
            "\", response=\"" + responseHash + "\", algorithm=" + algorithm;
        return getWithAuth(PATH, header);
    }

    /** Digest exchange where H(A1) is a pre-computed stored value (RFC 2617 "MD5:" credential:
     *  the stored digest is itself used directly as H(A1)). */
    public HttpTester.Response digestPreHashed(String user, String ha1Hex) throws Exception
    {
        HttpTester.Response challenge = get(PATH);
        String nonce = param(challenge.get(HttpHeader.WWW_AUTHENTICATE), "nonce");
        String qop = "auth";
        String nc = "00000001";
        String cnonce = "clientnonce";
        String uri = PATH;
        String ha2 = hashHex("MD5", ("GET:" + uri).getBytes(StandardCharsets.ISO_8859_1));
        String responseHash = hashHex("MD5",
            (ha1Hex + ":" + nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + ha2).getBytes(StandardCharsets.ISO_8859_1));
        String header = "Digest username=\"" + user + "\", realm=\"" + REALM + "\", nonce=\"" + nonce +
            "\", uri=\"" + uri + "\", qop=" + qop + ", nc=" + nc + ", cnonce=\"" + cnonce +
            "\", response=\"" + responseHash + "\", algorithm=MD5";
        return getWithAuth(PATH, header);
    }

    // ---- hashing helpers ----------------------------------------------------

    public static String hashHex(String algorithm, byte[] data) throws Exception
    {
        MessageDigest md = MessageDigest.getInstance(algorithm);
        return toHex(md.digest(data));
    }

    public static String toHex(byte[] bytes)
    {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes)
            sb.append(Character.forDigit((b >> 4) & 0xF, 16)).append(Character.forDigit(b & 0xF, 16));
        return sb.toString();
    }

    private static String param(String header, String name)
    {
        Matcher m = Pattern.compile(name + "=\"?([^\",]+)\"?").matcher(header);
        if (m.find())
            return m.group(1);
        return null;
    }

    // ---- assertions helpers -------------------------------------------------

    public static boolean authenticatedAs(HttpTester.Response r, String user)
    {
        return r.getStatus() == 200 && r.getContent() != null && r.getContent().contains("AUTHED:" + user);
    }

    public static boolean clientRefusal(HttpTester.Response r)
    {
        int s = r.getStatus();
        boolean authed = r.getContent() != null && r.getContent().contains("AUTHED:");
        return !authed && s >= 400 && s < 500;
    }
}
