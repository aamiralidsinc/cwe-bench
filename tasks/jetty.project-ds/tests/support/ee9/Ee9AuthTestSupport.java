package org.eclipse.jetty.ee9.security;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.eclipse.jetty.ee9.nested.AbstractHandler;
import org.eclipse.jetty.ee9.nested.ContextHandler;
import org.eclipse.jetty.ee9.nested.Request;
import org.eclipse.jetty.ee9.nested.ServletConstraint;
import org.eclipse.jetty.ee9.nested.SessionHandler;
import org.eclipse.jetty.security.AbstractLoginService;
import org.eclipse.jetty.security.LoginService;
import org.eclipse.jetty.security.RolePrincipal;
import org.eclipse.jetty.security.UserPrincipal;
import org.eclipse.jetty.security.UserStore;
import org.eclipse.jetty.server.Connector;
import org.eclipse.jetty.server.LocalConnector;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.util.TypeUtil;
import org.eclipse.jetty.util.security.Credential;

/**
 * Test-only fixture for the servlet-environment security handler: a real HTTP
 * server (LocalConnector) whose single protected path is guarded by the
 * authenticator under test.
 */
final class Ee9AuthTestSupport
{
    static final String REALM = "TestRealm";
    static final String USER = "user";
    static final String PATH = "/ctx/any/user";

    private static final Pattern NONCE = Pattern.compile("nonce=\"([^\"]*)\"");

    private Ee9AuthTestSupport()
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

    static final class OkHandler extends AbstractHandler
    {
        @Override
        public void handle(String target, Request baseRequest, HttpServletRequest request, HttpServletResponse response)
            throws IOException, ServletException
        {
            baseRequest.setHandled(true);
            String user = request.getRemoteUser();
            response.setStatus(200);
            response.setContentType("text/plain");
            response.getWriter().println(user == null ? "ANONYMOUS" : "OK " + user);
        }
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

        ConstraintSecurityHandler security = new ConstraintSecurityHandler();
        security.setLoginService(loginService);
        security.setAuthenticator(authenticator);

        ServletConstraint anyUser = new ServletConstraint();
        anyUser.setAuthenticate(true);
        anyUser.setName("anyUser");
        anyUser.setRoles(new String[]{ServletConstraint.ANY_ROLE});
        ConstraintMapping mapping = new ConstraintMapping();
        mapping.setPathSpec("/any/*");
        mapping.setConstraint(anyUser);
        security.setConstraintMappings(List.of(mapping), Set.of("user"));
        security.setHandler(new OkHandler());

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

    static String digestAuthorization(String algorithm, String username, String realm, String password,
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
        String response = TypeUtil.toString(md.digest(kd.getBytes(StandardCharsets.ISO_8859_1)), 16);
        return "Authorization: Digest username=\"" + username + "\", realm=\"" + realm +
            "\", nonce=\"" + nonce + "\", uri=\"" + uri + "\", algorithm=" + algorithm +
            ", qop=auth, nc=" + nc + ", cnonce=\"" + cnonce + "\", response=\"" + response + "\"";
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

    static String hex(byte[] bytes)
    {
        return TypeUtil.toString(bytes, 16);
    }
}
