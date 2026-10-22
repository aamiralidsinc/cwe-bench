package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.eclipse.jetty.util.security.Password;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The reported route: an HTTP Digest challenge/response handled by the core
 * server's security handler, with the secret held as a plain password in the
 * user store.
 */
public class SecurityDigestEncodingTest
{
    private static final String REAL_PASSWORD = "pa€";   // pa + euro sign
    private static final String WRONG_PASSWORD = "pa?";       // a different password
    private static final String CNONCE = "abcdef0123456789";

    @Test
    public void wrongPasswordThatCollapsesUnderTheLegacyEncodingIsRejected() throws Exception
    {
        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        login.putUser(AuthTestSupport.USER, new Password(REAL_PASSWORD), new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            String nonce = AuthTestSupport.nonce(fixture.get(null));
            String authorization = AuthTestSupport.digestAuthorization(
                "MD5", AuthTestSupport.USER, AuthTestSupport.REALM, WRONG_PASSWORD,
                StandardCharsets.ISO_8859_1, "GET", AuthTestSupport.PATH, nonce, "1", CNONCE);

            String response = fixture.get(authorization);
            assertTrue(AuthTestSupport.isClientError(response),
                "a wrong password must not be accepted: " + response);
            assertFalse(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a wrong password must not establish an identity: " + response);
        }
    }

    @Test
    public void wrongPasswordThatCollapsesUnderTheLegacyEncodingIsRejectedWhenAlgorithmIsOmitted() throws Exception
    {
        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        login.putUser(AuthTestSupport.USER, new Password(REAL_PASSWORD), new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            String nonce = AuthTestSupport.nonce(fixture.get(null));
            String authorization = AuthTestSupport.digestAuthorizationWithoutAlgorithm(
                AuthTestSupport.USER, AuthTestSupport.REALM, WRONG_PASSWORD,
                StandardCharsets.ISO_8859_1, "GET", AuthTestSupport.PATH, nonce, "1", CNONCE);

            String response = fixture.get(authorization);
            assertTrue(AuthTestSupport.isClientError(response),
                "a wrong password must not be accepted: " + response);
            assertFalse(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a wrong password must not establish an identity: " + response);
        }
    }

    @Test
    public void wrongPasswordIsRejectedWhenTheStrongerDigestAlgorithmIsSelected() throws Exception
    {
        DigestAuthenticator authenticator = new DigestAuthenticator();
        authenticator.setAlgorithm("SHA-256");

        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        login.putUser(AuthTestSupport.USER, new Password(REAL_PASSWORD), new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, authenticator))
        {
            String challenge = fixture.get(null);
            assertTrue(challenge.contains("SHA-256"),
                "the challenge must advertise the configured algorithm: " + challenge);
            String nonce = AuthTestSupport.nonce(challenge);
            String authorization = AuthTestSupport.digestAuthorization(
                "SHA-256", AuthTestSupport.USER, AuthTestSupport.REALM, WRONG_PASSWORD,
                StandardCharsets.ISO_8859_1, "GET", AuthTestSupport.PATH, nonce, "1", CNONCE);

            String response = fixture.get(authorization);
            assertTrue(AuthTestSupport.isClientError(response),
                "a wrong password must not be accepted: " + response);
            assertFalse(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a wrong password must not establish an identity: " + response);
        }
    }
}
