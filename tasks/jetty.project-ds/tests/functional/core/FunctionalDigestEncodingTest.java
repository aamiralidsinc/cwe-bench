package org.eclipse.jetty.security;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.eclipse.jetty.util.security.Credential;
import org.eclipse.jetty.util.security.Password;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Legitimate Digest logins that must keep working after the fix.
 */
public class FunctionalDigestEncodingTest
{
    private static final String CNONCE = "abcdef0123456789";

    private static String attempt(AuthTestSupport.Fixture fixture, String algorithm,
                                String password, Charset passwordCharset) throws Exception
    {
        String nonce = AuthTestSupport.nonce(fixture.get(null));
        String authorization = AuthTestSupport.digestAuthorization(
            algorithm, AuthTestSupport.USER, AuthTestSupport.REALM, password,
            passwordCharset, "GET", AuthTestSupport.PATH, nonce, "1", CNONCE);
        return fixture.get(authorization);
    }

    @Test
    public void correctPasswordIsAccepted() throws Exception
    {
        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        login.putUser(AuthTestSupport.USER, new Password("password"), new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            String response = attempt(fixture, "MD5", "password", StandardCharsets.UTF_8);
            assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "the correct password must authenticate: " + response);
        }
    }

    @Test
    public void nonAsciiPasswordIsAcceptedWithTheServerEncoding() throws Exception
    {
        String password = "pa€";
        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        login.putUser(AuthTestSupport.USER, new Password(password), new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            // The client and server must agree on how the password characters are
            // encoded into the digest. Either agreement is acceptable; rejecting the
            // account outright is not.
            boolean accepted =
                AuthTestSupport.authenticatedAs(
                    attempt(fixture, "MD5", password, StandardCharsets.ISO_8859_1), AuthTestSupport.USER) ||
                AuthTestSupport.authenticatedAs(
                    attempt(fixture, "MD5", password, StandardCharsets.UTF_8), AuthTestSupport.USER);
            assertTrue(accepted, "a legitimate non-ASCII password must still authenticate");
        }
    }

    @Test
    public void preHashedDigestCredentialIsAccepted() throws Exception
    {
        String a1 = AuthTestSupport.USER + ":" + AuthTestSupport.REALM + ":password";
        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        login.putUser(AuthTestSupport.USER,
            Credential.getCredential("MD5:" + AuthTestSupport.hex(AuthTestSupport.md5(a1))),
            new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            String response = attempt(fixture, "MD5", "password", StandardCharsets.UTF_8);
            assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "a pre-hashed digest credential must be used as the response hash: " + response);
        }
    }

    @Test
    public void correctPasswordIsAcceptedWithTheStrongerAlgorithm() throws Exception
    {
        DigestAuthenticator authenticator = new DigestAuthenticator();
        authenticator.setAlgorithm("SHA-256");

        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        login.putUser(AuthTestSupport.USER, new Password("password"), new String[]{"user"});

        try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, authenticator))
        {
            String challenge = fixture.get(null);
            assertTrue(challenge.contains("SHA-256"),
                "the challenge must advertise the configured algorithm: " + challenge);
            String response = attempt(fixture, "SHA-256", "password", StandardCharsets.UTF_8);
            assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                "the correct password must authenticate with the stronger algorithm: " + response);
        }
    }
}
