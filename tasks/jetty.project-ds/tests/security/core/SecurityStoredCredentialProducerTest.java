package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.eclipse.jetty.util.security.Credential;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The stored credential is minted from the account's real secret by the
 * server's own password-preparation path (the one an administrator runs to
 * produce a stored value), then presented over HTTP Basic. Because that path
 * and the checking path must agree on the exact bytes of the secret, a fix
 * confined to the checking side still accepts a different value that the
 * legacy representation collapses onto the stored bytes.
 */
public class SecurityStoredCredentialProducerTest
{
    private static final String REAL_PASSWORD = "pa€";  // the account's configured secret
    private static final String WRONG_PASSWORD = "pa?";  // a different value

    private static BasicAuthenticator basicAuthenticator()
    {
        BasicAuthenticator authenticator = new BasicAuthenticator();
        authenticator.setCharset(StandardCharsets.UTF_8);
        return authenticator;
    }

    @Test
    public void wrongPasswordIsRejectedWhenTheStoredDigestWasProducedFromANonAsciiSecret() throws Exception
    {
        String produced = Credential.MD5.digest(REAL_PASSWORD);
        assertTrue(produced != null && produced.startsWith("MD5:"),
            "preparing the account's stored secret must yield a stored credential: " + produced);

        AuthTestSupport.StoreLoginService login = new AuthTestSupport.StoreLoginService();
        login.putUser(AuthTestSupport.USER, Credential.getCredential(produced), new String[]{"user"});

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
