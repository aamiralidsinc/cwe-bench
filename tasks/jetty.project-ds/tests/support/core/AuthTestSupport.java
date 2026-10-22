package org.eclipse.jetty.security;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.jetty.util.resource.ResourceFactory;

import org.eclipse.jetty.http.HttpHeader;
import org.eclipse.jetty.io.Content;
import org.eclipse.jetty.server.Connector;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.LocalConnector;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.server.handler.ContextHandler;
import org.eclipse.jetty.session.SessionHandler;
import org.eclipse.jetty.util.Callback;
import org.eclipse.jetty.util.TypeUtil;
import org.eclipse.jetty.util.security.Credential;

/**
 * Test-only fixture: a real HTTP server (LocalConnector) whose single protected
 * path is guarded by the authenticator under test and whose login service reads
 * a real user store. No product test helpers are used so the suite is
 * self-contained.
 */
final class AuthTestSupport
{
    static final String REALM = "TestRealm";
    static final String USER = "user";
    static final String PATH = "/ctx/any/user";

    private static final Pattern NONCE = Pattern.compile("nonce=\"([^\"]*)\"");

    private AuthTestSupport()
    {
    }

    static final class StoreLoginService extends AbstractLoginService
    {
        private final UserStore _store = new UserStore();

        StoreLoginService()
        {
            setName(REALM);
        }

        void putUser(String name, Credential credential, String[] roles)
        {
            _store.addUser(name, credential, roles);
        }

        @Override
        protected List<RolePrincipal> loadRoleInfo(UserPrincipal user)
        {
            return _store.getRolePrincipals(user.getName());
        }

        @Override
        protected UserPrincipal loadUserInfo(String userName)
        {
            return _store.getUserPrincipal(userName);
        }
    }

    static final class Fixture implements AutoCloseable
    {
        final Server server;
        final LocalConnector connector;

        Fixture(Server server, LocalConnector connector)
        {
            this.server = server;
            this.connector = connector;
        }

        String get(String authorizationHeader) throws Exception
        {
            String request = "GET " + PATH + " HTTP/1.0\r\n";
            if (authorizationHeader != null)
                request += authorizationHeader + "\r\n";
            request += "\r\n";
            return connector.getResponse(request);
        }

        @Override
        public void close() throws Exception
        {
            server.stop();
        }
    }

    static final class MarkerHandler extends Handler.Abstract
    {
        @Override
        public boolean handle(Request request, Response response, Callback callback)
        {
            AuthenticationState state = AuthenticationState.getAuthenticationState(request);
            String user = null;
            if (state instanceof AuthenticationState.Succeeded succeeded)
                user = succeeded.getUserIdentity().getUserPrincipal().getName();
            response.getHeaders().add(HttpHeader.CONTENT_TYPE, "text/plain");
            Content.Sink.write(response, true, user == null ? "ANONYMOUS" : "OK " + user, callback);
            return true;
        }
    }

    /**
     * Write a real realm properties file (exactly the bytes given; callers use Java
     * properties escapes so that significant characters survive the file format) and
     * return the login service that reads it.
     */
    static Path writeConfig(String content) throws IOException
    {
        Path config = Files.createTempFile("jetty-realm", ".properties");
        Files.write(config, content.getBytes(StandardCharsets.US_ASCII));
        return config;
    }

    static HashLoginService hashLoginService(Path config)
    {
        HashLoginService login = new HashLoginService(REALM);
        login.setConfig(ResourceFactory.root().newResource(config));
        return login;
    }

    static Fixture start(LoginService loginService, Authenticator authenticator) throws Exception
    {
        Server server = new Server();
        LocalConnector connector = new LocalConnector(server);
        server.setConnectors(new Connector[]{connector});

        ContextHandler context = new ContextHandler();
        context.setContextPath("/ctx");
        SessionHandler sessions = new SessionHandler();
        context.setHandler(sessions);

        SecurityHandler.PathMapped security = new SecurityHandler.PathMapped();
        security.put("/any/*", Constraint.ANY_USER);
        security.setAuthenticator(authenticator);
        security.setLoginService(loginService);
        security.setHandler(new MarkerHandler());
        sessions.setHandler(security);

        server.setHandler(context);
        server.start();
        return new Fixture(server, connector);
    }

    static String nonce(String challengeResponse)
    {
        Matcher matcher = NONCE.matcher(challengeResponse);
        if (!matcher.find())
            throw new IllegalStateException("no nonce in: " + challengeResponse);
        return matcher.group(1);
    }

    static String basic(String username, String password, Charset charset)
    {
        return "Authorization: Basic " + Base64.getEncoder().encodeToString((username + ":" + password).getBytes(charset));
    }

    static String digestAuthorization(String algorithm, String username, String realm, String password,
                                      Charset passwordCharset, String method, String uri,
                                      String nonce, String nc, String cnonce)
        throws Exception
    {
        String response = digestResponse(algorithm, username, realm, password, passwordCharset,
            method, uri, nonce, nc, cnonce);
        return "Authorization: Digest username=\"" + username + "\", realm=\"" + realm +
            "\", nonce=\"" + nonce + "\", uri=\"" + uri + "\", algorithm=" + algorithm +
            ", qop=auth, nc=" + nc + ", cnonce=\"" + cnonce + "\", response=\"" + response + "\"";
    }

    static String digestAuthorizationWithoutAlgorithm(String username, String realm, String password,
                                                     Charset passwordCharset, String method, String uri,
                                                     String nonce, String nc, String cnonce)
        throws Exception
    {
        String response = digestResponse("MD5", username, realm, password, passwordCharset,
            method, uri, nonce, nc, cnonce);
        return "Authorization: Digest username=\"" + username + "\", realm=\"" + realm +
            "\", nonce=\"" + nonce + "\", uri=\"" + uri +
            "\", qop=auth, nc=" + nc + ", cnonce=\"" + cnonce + "\", response=\"" + response + "\"";
    }

    static String digestResponse(String algorithm, String username, String realm, String password,
                                 Charset passwordCharset, String method, String uri,
                                 String nonce, String nc, String cnonce)
        throws Exception
    {
        MessageDigest md = MessageDigest.getInstance(algorithm);
        byte[] ha1 = md.digest((username + ":" + realm + ":" + password).getBytes(passwordCharset));
        md.reset();
        byte[] ha2 = md.digest((method + ":" + uri).getBytes(StandardCharsets.ISO_8859_1));
        String kd = TypeUtil.toString(ha1, 16) + ":" + nonce + ":" + nc + ":" + cnonce +
            ":auth:" + TypeUtil.toString(ha2, 16);
        return TypeUtil.toString(md.digest(kd.getBytes(StandardCharsets.ISO_8859_1)), 16);
    }

    static int status(String response)
    {
        int first = response.indexOf(' ');
        int second = response.indexOf(' ', first + 1);
        if (first < 0 || second < 0)
            throw new IllegalStateException("no status line in: " + response);
        return Integer.parseInt(response.substring(first + 1, second));
    }

    static boolean isClientError(String response)
    {
        int status = status(response);
        return status >= 400 && status < 500;
    }

    static boolean isOk(String response)
    {
        return status(response) == 200;
    }

    static boolean authenticatedAs(String response, String username)
    {
        return isOk(response) && response.contains("OK " + username);
    }

    static byte[] md5(String text)
        throws Exception
    {
        return MessageDigest.getInstance("MD5").digest(text.getBytes(StandardCharsets.ISO_8859_1));
    }

    static byte[] sha256(String text)
        throws Exception
    {
        return MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.ISO_8859_1));
    }

    static String hex(byte[] bytes)
    {
        return TypeUtil.toString(bytes, 16);
    }
}
