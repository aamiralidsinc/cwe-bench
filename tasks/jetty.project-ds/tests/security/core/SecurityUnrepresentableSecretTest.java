package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The configured secret contains a character that the representation used to
 * hash it cannot carry. A different value that the representation degrades to
 * the same bytes must not establish the account's identity.
 */
public class SecurityUnrepresentableSecretTest
{
    // The configured secret is "pa" followed by one lone surrogate code unit,
    // written with the properties escape so that the value itself holds it.
    private static final String CONFIG = "user: pa\\uD800,user\n";
    private static final String WRONG_PASSWORD = "pa?";
    private static final String CNONCE = "abcdef0123456789";

    @Test
    public void valueThatCollapsesOntoAnUnrepresentableSecretIsRejected() throws Exception
    {
        Path config = AuthTestSupport.writeConfig(CONFIG);
        try
        {
            HashLoginService login = AuthTestSupport.hashLoginService(config);

            try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, new DigestAuthenticator()))
            {
                String nonce = AuthTestSupport.nonce(fixture.get(null));
                String authorization = AuthTestSupport.digestAuthorization(
                    "MD5", AuthTestSupport.USER, AuthTestSupport.REALM, WRONG_PASSWORD,
                    StandardCharsets.UTF_8, "GET", AuthTestSupport.PATH, nonce, "1", CNONCE);

                String response = fixture.get(authorization);
                assertTrue(AuthTestSupport.isClientError(response),
                    "a value that is not exactly the configured secret must not be accepted: " + response);
                assertFalse(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                    "a value that is not exactly the configured secret must not establish an identity: " + response);
            }
        }
        finally
        {
            Files.deleteIfExists(config);
        }
    }
}
