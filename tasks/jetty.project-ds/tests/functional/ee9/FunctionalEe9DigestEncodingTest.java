package org.eclipse.jetty.ee9.security;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.ee9.security.authentication.DigestAuthenticator;
import org.eclipse.jetty.util.security.Credential;
import org.eclipse.jetty.util.security.Password;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Legitimate Digest logins through the servlet-environment security handler.
 */
public class FunctionalEe9DigestEncodingTest
{
    private static final String CNONCE = "abcdef0123456789";

    private static String attempt(Ee9AuthTestSupport.Fixture fixture, String password, Charset passwordCharset)
        throws Exception
    {
        String nonce = Ee9AuthTestSupport.nonce(fixture.get(null));
        String authorization = Ee9AuthTestSupport.digestAuthorization(
            "MD5", Ee9AuthTestSupport.USER, Ee9AuthTestSupport.REALM, password,
            passwordCharset, "GET", Ee9AuthTestSupport.PATH, nonce, "1", CNONCE);
        return fixture.get(authorization);
    }

    @Test
    public void correctPasswordIsAccepted() throws Exception
    {
        Ee9AuthTestSupport.StoreLoginService login = new Ee9AuthTestSupport.StoreLoginService();
        login.putUser(Ee9AuthTestSupport.USER, new Password("password"), new String[]{"user"});

        try (Ee9AuthTestSupport.Fixture fixture = Ee9AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            String response = attempt(fixture, "password", StandardCharsets.UTF_8);
            assertTrue(Ee9AuthTestSupport.authenticatedAs(response, Ee9AuthTestSupport.USER),
                "the correct password must authenticate: " + response);
        }
    }

    @Test
    public void nonAsciiPasswordIsAcceptedWithTheServerEncoding() throws Exception
    {
        String password = "pa€";
        Ee9AuthTestSupport.StoreLoginService login = new Ee9AuthTestSupport.StoreLoginService();
        login.putUser(Ee9AuthTestSupport.USER, new Password(password), new String[]{"user"});

        try (Ee9AuthTestSupport.Fixture fixture = Ee9AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            boolean accepted =
                Ee9AuthTestSupport.authenticatedAs(
                    attempt(fixture, password, StandardCharsets.ISO_8859_1), Ee9AuthTestSupport.USER) ||
                Ee9AuthTestSupport.authenticatedAs(
                    attempt(fixture, password, StandardCharsets.UTF_8), Ee9AuthTestSupport.USER);
            assertTrue(accepted, "a legitimate non-ASCII password must still authenticate");
        }
    }

    @Test
    public void preHashedDigestCredentialIsAccepted() throws Exception
    {
        String a1 = Ee9AuthTestSupport.USER + ":" + Ee9AuthTestSupport.REALM + ":password";
        Ee9AuthTestSupport.StoreLoginService login = new Ee9AuthTestSupport.StoreLoginService();
        login.putUser(Ee9AuthTestSupport.USER,
            Credential.getCredential("MD5:" + Ee9AuthTestSupport.hex(Ee9AuthTestSupport.md5(a1))),
            new String[]{"user"});

        try (Ee9AuthTestSupport.Fixture fixture = Ee9AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            String response = attempt(fixture, "password", StandardCharsets.UTF_8);
            assertTrue(Ee9AuthTestSupport.authenticatedAs(response, Ee9AuthTestSupport.USER),
                "a pre-hashed digest credential must be used as the response hash: " + response);
        }
    }
}
