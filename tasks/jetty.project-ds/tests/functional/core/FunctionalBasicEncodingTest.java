package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.eclipse.jetty.util.security.Credential;
import org.eclipse.jetty.util.security.Password;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Legitimate HTTP Basic logins that must keep working after the fix.
 */
public class FunctionalBasicEncodingTest
{
    private static BasicAuthenticator basicAuthenticator()
    {
        BasicAuthenticator authenticator = new BasicAuthenticator();
        authenticator.setCharset(StandardCharsets.UTF_8);
        return authenticator;
    }

    @Test
    public void correctPasswordIsAccepted() throws Exception
    {
        AuthTestSupport.StoreLoginService loginService = new AuthTestSupport.StoreLoginService();
        loginService.putUser(AuthTestSupport.USER, new Password("password"), new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(loginService, basicAuthenticator()))
        {
            String response = fixture.get(AuthTestSupport.basic(
                AuthTestSupport.USER, "password", StandardCharsets.UTF_8));
            assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "the correct password must authenticate: " + response);
        }
    }

    @Test
    public void nonAsciiPlainPasswordIsAccepted() throws Exception
    {
        String password = "pa€";
        AuthTestSupport.StoreLoginService loginService = new AuthTestSupport.StoreLoginService();
        loginService.putUser(AuthTestSupport.USER, new Password(password), new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(loginService, basicAuthenticator()))
        {
            String response = fixture.get(AuthTestSupport.basic(
                AuthTestSupport.USER, password, StandardCharsets.UTF_8));
            assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a legitimate non-ASCII password must still authenticate: " + response);
        }
    }

    @Test
    public void storedDigestCredentialIsAccepted() throws Exception
    {
        AuthTestSupport.StoreLoginService loginService = new AuthTestSupport.StoreLoginService();
        loginService.putUser(AuthTestSupport.USER,
            Credential.getCredential("MD5:" + AuthTestSupport.hex(AuthTestSupport.md5("password"))),
            new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(loginService, basicAuthenticator()))
        {
            String response = fixture.get(AuthTestSupport.basic(
                AuthTestSupport.USER, "password", StandardCharsets.UTF_8));
            assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a stored digest credential must accept the correct password: " + response);
        }
    }

    @Test
    public void storedStrongDigestCredentialIsAccepted() throws Exception
    {
        AuthTestSupport.StoreLoginService loginService = new AuthTestSupport.StoreLoginService();
        loginService.putUser(AuthTestSupport.USER,
            Credential.getCredential("SHA256:" + AuthTestSupport.hex(AuthTestSupport.sha256("password"))),
            new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(loginService, basicAuthenticator()))
        {
            String response = fixture.get(AuthTestSupport.basic(
                AuthTestSupport.USER, "password", StandardCharsets.UTF_8));
            assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a stored strong digest credential must accept the correct password: " + response);
        }
    }
}
