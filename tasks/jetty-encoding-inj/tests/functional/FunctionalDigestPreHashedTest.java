package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/**
 * Coupled contract: an account whose stored secret is a pre-computed digest of
 * user:realm:password (used directly, without re-hashing a plaintext password)
 * must keep authenticating exactly as before.
 */
public class FunctionalDigestPreHashedTest
{
    @Test
    public void preHashedCredentialStillAuthenticates() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new DigestAuthenticator()))
        {
            // H(A1) = MD5("carol:TestRealm:passphrase"), stored directly.
            String ha1 = DigestEncHarness.hashHex("MD5",
                ("carol:" + DigestEncHarness.REALM + ":passphrase").getBytes(StandardCharsets.ISO_8859_1));
            h.addUser("carol", "MD5:" + ha1);
            HttpTester.Response r = h.digestPreHashed("carol", ha1);
            assertThat(DigestEncHarness.authenticatedAs(r, "carol"), is(true));
        }
    }
}
