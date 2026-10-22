package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The account's secret is stored through the deployment's real user
 * configuration. A presented value that is not exactly that secret must not
 * establish the account's identity, even when it differs only in a character
 * that the configuration layer would normally discard as formatting.
 */
public class SecurityConfiguredSecretExactnessTest
{
    // The configured value is "pa? " - the trailing space is written with an
    // explicit properties escape, so it is part of the value, not layout.
    private static final String CONFIG = "user: pa?\\u0020,user\n";
    private static final String WRONG_PASSWORD = "pa?";

    @Test
    public void valueThatDropsAConfiguredCharacterIsRejected() throws Exception
    {
        Path config = AuthTestSupport.writeConfig(CONFIG);
        try
        {
            HashLoginService login = AuthTestSupport.hashLoginService(config);
            BasicAuthenticator authenticator = new BasicAuthenticator();
            authenticator.setCharset(StandardCharsets.UTF_8);

            try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, authenticator))
            {
                String response = fixture.get(AuthTestSupport.basic(
                    AuthTestSupport.USER, WRONG_PASSWORD, StandardCharsets.UTF_8));
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
