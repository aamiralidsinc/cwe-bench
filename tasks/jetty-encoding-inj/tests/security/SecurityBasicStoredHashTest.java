package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/**
 * User/password login against an account whose stored secret uses an alternative
 * hashed-password format: the Latin-1 collision must not be accepted here either.
 */
public class SecurityBasicStoredHashTest
{
    static final String REAL = "secret€€";
    static final String FORGED = "secret✓✓";

    @Test
    public void nonLatin1PasswordCollisionIsRefused() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new BasicAuthenticator(), StandardCharsets.UTF_8))
        {
            String stored = "SHA1:" + DigestEncHarness.hashHex("SHA-1", REAL.getBytes(StandardCharsets.ISO_8859_1));
            h.addUser("victim", stored);
            String header = DigestEncHarness.basicHeader("victim", FORGED, StandardCharsets.UTF_8);
            HttpTester.Response r = h.getWithAuth(DigestEncHarness.PATH, header);
            assertThat("forged credential must not authenticate as the victim",
                DigestEncHarness.clientRefusal(r), is(true));
        }
    }
}
