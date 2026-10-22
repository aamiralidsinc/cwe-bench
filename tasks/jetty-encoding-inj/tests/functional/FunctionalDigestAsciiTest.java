package org.eclipse.jetty.security;

import java.nio.charset.StandardCharsets;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/** A legitimate challenge-response login with the correct password still works. */
public class FunctionalDigestAsciiTest
{
    @Test
    public void correctPasswordAuthenticates() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new DigestAuthenticator()))
        {
            h.addUser("alice", "correct-horse");
            HttpTester.Response r = h.digest("alice", "correct-horse", "MD5", StandardCharsets.UTF_8);
            assertThat(DigestEncHarness.authenticatedAs(r, "alice"), is(true));
        }
    }

    @Test
    public void wrongPasswordIsRefused() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new DigestAuthenticator()))
        {
            h.addUser("alice", "correct-horse");
            HttpTester.Response r = h.digest("alice", "wrong-horse", "MD5", StandardCharsets.UTF_8);
            assertThat(DigestEncHarness.clientRefusal(r), is(true));
        }
    }
}
