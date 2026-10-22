package org.eclipse.jetty.security;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * A legitimate secret that contains a supplementary character (a valid
 * surrogate pair) must still authenticate. The client and server must agree on
 * how the characters are encoded; refusing the account outright is not
 * acceptable.
 */
public class FunctionalUnrepresentableNeighbourTest
{
    private static final String CNONCE = "abcdef0123456789";

    private static String attempt(AuthTestSupport.Fixture fixture, String password, Charset passwordCharset)
        throws Exception
    {
        String nonce = AuthTestSupport.nonce(fixture.get(null));
        String authorization = AuthTestSupport.digestAuthorization(
            "MD5", AuthTestSupport.USER, AuthTestSupport.REALM, password,
            passwordCharset, "GET", AuthTestSupport.PATH, nonce, "1", CNONCE);
        return fixture.get(authorization);
    }

    @Test
    public void supplementaryCharacterSecretIsAcceptedWithAnAgreedEncoding() throws Exception
    {
        // pa + U+1F600, carried by the configuration as its two surrogate escapes.
        String password = "pa😀";
        Path config = AuthTestSupport.writeConfig("user: pa\\uD83D\\uDE00,user\n");
        try
        {
            HashLoginService login = AuthTestSupport.hashLoginService(config);
            try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, new DigestAuthenticator()))
            {
                boolean accepted =
                    AuthTestSupport.authenticatedAs(
                        attempt(fixture, password, StandardCharsets.ISO_8859_1), AuthTestSupport.USER) ||
                    AuthTestSupport.authenticatedAs(
                        attempt(fixture, password, StandardCharsets.UTF_8), AuthTestSupport.USER);
                assertTrue(accepted, "a legitimate supplementary-character secret must still authenticate");
            }
        }
        finally
        {
            Files.deleteIfExists(config);
        }
    }
}
