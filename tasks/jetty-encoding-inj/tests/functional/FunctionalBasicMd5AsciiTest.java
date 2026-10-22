package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/** A legitimate user/password login against a hashed-password account still works. */
public class FunctionalBasicMd5AsciiTest
{
    @Test
    public void correctPasswordAuthenticates() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new BasicAuthenticator(), StandardCharsets.UTF_8))
        {
            String stored = "MD5:" + DigestEncHarness.hashHex("MD5", "s3cr3t".getBytes(StandardCharsets.UTF_8));
            h.addUser("bob", stored);
            String header = DigestEncHarness.basicHeader("bob", "s3cr3t", StandardCharsets.UTF_8);
            HttpTester.Response r = h.getWithAuth(DigestEncHarness.PATH, header);
            assertThat(DigestEncHarness.authenticatedAs(r, "bob"), is(true));
        }
    }
}
