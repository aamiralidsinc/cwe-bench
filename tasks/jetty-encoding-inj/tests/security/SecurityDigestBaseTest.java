package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/**
 * Challenge-response login: a credential that differs from the account's real secret
 * only in characters outside the Latin-1 range must not be accepted as that account.
 */
public class SecurityDigestBaseTest
{
    // Account's real password and a DIFFERENT one that shares its lossy Latin-1 projection.
    static final String REAL = "secret€€";       // U+20AC (euro sign)
    static final String FORGED = "secret✓✓";     // U+2713 (check mark)

    @Test
    public void nonLatin1PasswordCollisionIsRefused() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new DigestAuthenticator()))
        {
            h.addUser("victim", REAL);
            // Attacker encodes the forged password with the legacy single-byte charset.
            HttpTester.Response r = h.digest("victim", FORGED, "MD5", StandardCharsets.ISO_8859_1);
            assertThat("forged credential must not authenticate as the victim",
                DigestEncHarness.clientRefusal(r), is(true));
        }
    }
}
