package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/**
 * Challenge-response login negotiated with the stronger hash algorithm: the same
 * collision must not let a credential differing only outside Latin-1 authenticate.
 */
public class SecurityDigestAltAlgorithmTest
{
    static final String REAL = "secret€€";
    static final String FORGED = "secret✓✓";

    @Test
    public void nonLatin1PasswordCollisionIsRefused() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new DigestAuthenticator()))
        {
            h.addUser("victim", REAL);
            HttpTester.Response r = h.digest("victim", FORGED, "SHA-256", StandardCharsets.ISO_8859_1);
            assertThat("forged credential must not authenticate as the victim",
                DigestEncHarness.clientRefusal(r), is(true));
        }
    }
}
