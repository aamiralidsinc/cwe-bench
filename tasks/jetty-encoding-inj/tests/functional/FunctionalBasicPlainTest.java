package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.BasicAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/** A legitimate user/password login against a plaintext-stored account still works,
 *  and a wrong password is still refused. */
public class FunctionalBasicPlainTest
{
    @Test
    public void correctPasswordAuthenticates() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new BasicAuthenticator()))
        {
            h.addUser("dave", "letmein");
            String header = DigestEncHarness.basicHeader("dave", "letmein", StandardCharsets.ISO_8859_1);
            HttpTester.Response r = h.getWithAuth(DigestEncHarness.PATH, header);
            assertThat(DigestEncHarness.authenticatedAs(r, "dave"), is(true));
        }
    }

    @Test
    public void wrongPasswordIsRefused() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new BasicAuthenticator()))
        {
            h.addUser("dave", "letmein");
            String header = DigestEncHarness.basicHeader("dave", "nope", StandardCharsets.ISO_8859_1);
            HttpTester.Response r = h.getWithAuth(DigestEncHarness.PATH, header);
            assertThat(DigestEncHarness.clientRefusal(r), is(true));
        }
    }
}
