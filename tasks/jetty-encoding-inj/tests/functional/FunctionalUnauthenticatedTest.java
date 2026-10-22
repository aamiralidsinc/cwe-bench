package org.eclipse.jetty.security;

import org.eclipse.jetty.http.HttpTester;
import org.eclipse.jetty.security.authentication.DigestAuthenticator;
import org.junit.jupiter.api.Test;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

/** A request with no credentials to a protected resource is challenged, not served. */
public class FunctionalUnauthenticatedTest
{
    @Test
    public void missingCredentialsAreChallenged() throws Exception
    {
        try (DigestEncHarness h = new DigestEncHarness(new DigestAuthenticator()))
        {
            h.addUser("eve", "pw");
            HttpTester.Response r = h.get(DigestEncHarness.PATH);
            assertThat(DigestEncHarness.clientRefusal(r), is(true));
        }
    }
}
