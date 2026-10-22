package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.eclipse.jetty.util.security.Credential;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * A route into the same password decision: a stored, pre-computed password
 * digest checked by an HTTP Basic login.
 */
public class SecurityStoredCredentialEncodingTest
{
    private static final String REAL_PASSWORD = "pa?";        // what the stored digest is of
    private static final String WRONG_PASSWORD = "pa€";  // a different password

    private static BasicAuthenticator basicAuthenticator()
    {
        BasicAuthenticator authenticator = new BasicAuthenticator();
        authenticator.setCharset(StandardCharsets.UTF_8);
        return authenticator;
    }

    @Test
    public void wrongPasswordThatCollapsesUnderTheLegacyEncodingIsRejectedForStoredDigest() throws Exception
    {
        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        Credential credential = Credential.getCredential("MD5:" + AuthTestSupport.hex(AuthTestSupport.md5(REAL_PASSWORD)));
        login.putUser(AuthTestSupport.USER, credential, new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, basicAuthenticator()))
        {
            String response = fixture.get(AuthTestSupport.basic(
                AuthTestSupport.USER, WRONG_PASSWORD, StandardCharsets.UTF_8));
            assertTrue(AuthTestSupport.isClientError(response),
                "a wrong password must not be accepted: " + response);
            assertFalse(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a wrong password must not establish an identity: " + response);
        }
    }

    @Test
    public void wrongPasswordThatCollapsesUnderTheLegacyEncodingIsRejectedForStoredStrongDigest() throws Exception
    {
        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        Credential credential = Credential.getCredential("SHA256:" + AuthTestSupport.hex(AuthTestSupport.sha256(REAL_PASSWORD)));
        login.putUser(AuthTestSupport.USER, credential, new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, basicAuthenticator()))
        {
            String response = fixture.get(AuthTestSupport.basic(
                AuthTestSupport.USER, WRONG_PASSWORD, StandardCharsets.UTF_8));
            assertTrue(AuthTestSupport.isClientError(response),
                "a wrong password must not be accepted: " + response);
            assertFalse(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a wrong password must not establish an identity: " + response);
        }
    }
}
