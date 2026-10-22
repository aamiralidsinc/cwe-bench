package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/**
 * User/password login against an account whose stored secret is a hashed password:
 * a submitted password that differs from the real one only outside the Latin-1 range
 * must not be accepted.
 */
public class SecurityBasicMd5RouteTest
{
    static final String REAL = "secret€€";
    static final String FORGED = "secret✓✓";

    @Test
    public void nonLatin1PasswordCollisionIsRefused() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new BasicAuthenticator(), StandardCharsets.UTF_8))
        {
            // Stored hash of the account's real password (as the password tool would produce it).
            String stored = "MD5:" + DigestEncHarness.hashHex("MD5", REAL.getBytes(StandardCharsets.ISO_8859_1));
            h.addUser("victim", stored);
            // Client sends the forged password over the wire using the advertised charset.
            String header = DigestEncHarness.basicHeader("victim", FORGED, StandardCharsets.UTF_8);
            HttpTester.Response r = h.getWithAuth(DigestEncHarness.PATH, header);
            assertThat("forged credential must not authenticate as the victim",
                DigestEncHarness.clientRefusal(r), is(true));
        }
    }
}
