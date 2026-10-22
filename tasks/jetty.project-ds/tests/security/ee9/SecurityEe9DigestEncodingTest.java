package org.eclipse.jetty.ee9.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.ee9.security.authentication.DigestAuthenticator;
import org.eclipse.jetty.util.security.Password;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The same password decision in the servlet-environment security handler.
 */
public class SecurityEe9DigestEncodingTest
{
    private static final String REAL_PASSWORD = "pa€";
    private static final String WRONG_PASSWORD = "pa?";
    private static final String CNONCE = "abcdef0123456789";

    @Test
    public void wrongPasswordThatCollapsesUnderTheLegacyEncodingIsRejected() throws Exception
    {
        Ee9AuthTestSupport.StoreLoginService login = new Ee9AuthTestSupport.StoreLoginService();
        login.putUser(Ee9AuthTestSupport.USER, new Password(REAL_PASSWORD), new String[]{"user"});

        try (Ee9AuthTestSupport.Fixture fixture = Ee9AuthTestSupport.start(login, new DigestAuthenticator()))
        {
            String nonce = Ee9AuthTestSupport.nonce(fixture.get(null));
            String authorization = Ee9AuthTestSupport.digestAuthorization(
                "MD5", Ee9AuthTestSupport.USER, Ee9AuthTestSupport.REALM, WRONG_PASSWORD,
                StandardCharsets.ISO_8859_1, "GET", Ee9AuthTestSupport.PATH, nonce, "1", CNONCE);

            String response = fixture.get(authorization);
            assertTrue(Ee9AuthTestSupport.isClientError(response),
                "a wrong password must not be accepted: " + response);
            assertFalse(Ee9AuthTestSupport.authenticatedAs(response, Ee9AuthTestSupport.USER),
                "a wrong password must not establish an identity: " + response);
        }
    }
}
