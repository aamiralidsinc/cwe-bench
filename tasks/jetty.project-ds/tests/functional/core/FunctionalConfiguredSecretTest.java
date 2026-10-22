package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Legitimate logins configured through the deployment's real user
 * configuration must keep working.
 */
public class FunctionalConfiguredSecretTest
{
    private static BasicAuthenticator basicAuthenticator()
    {
        BasicAuthenticator authenticator = new BasicAuthenticator();
        authenticator.setCharset(StandardCharsets.UTF_8);
        return authenticator;
    }

    @Test
    public void ordinaryConfiguredSecretIsAccepted() throws Exception
    {
        Path config = AuthTestSupport.writeConfig("user: password,user\n");
        try
        {
            HashLoginService login = AuthTestSupport.hashLoginService(config);
            try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, basicAuthenticator()))
            {
                String response = fixture.get(AuthTestSupport.basic(
                    AuthTestSupport.USER, "password", StandardCharsets.UTF_8));
                assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                    "the configured secret must authenticate: " + response);
            }
        }
        finally
        {
            Files.deleteIfExists(config);
        }
    }

    @Test
    public void nonAsciiConfiguredSecretIsAccepted() throws Exception
    {
        // paeuro: the configuration carries the character with an escape, and
        // the client and server agree on the UTF-8 representation.
        Path config = AuthTestSupport.writeConfig("user: pa\\u20AC,user\n");
        try
        {
            HashLoginService login = AuthTestSupport.hashLoginService(config);
            try (AuthTestSupport.Fixture fixture = AuthTestSupport.start(login, basicAuthenticator()))
            {
                String response = fixture.get(AuthTestSupport.basic(
                    AuthTestSupport.USER, "pa€", StandardCharsets.UTF_8));
                assertTrue(AuthTestSupport.authenticatedAs(response, AuthTestSupport.USER),
                    "a legitimate non-ASCII configured secret must authenticate: " + response);
            }
        }
        finally
        {
            Files.deleteIfExists(config);
        }
    }
}
