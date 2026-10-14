import org.asynchttpclient.*;
import io.netty.handler.codec.http.cookie.DefaultCookie;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.asynchttpclient.Dsl.*;
import static org.junit.jupiter.api.Assertions.*;

/**
 * The cookie feature must keep working: the store still contributes its cookies, request-list cookies
 * are still sent, a caller header with no competing store cookie is sent verbatim, and a session the
 * server rotates on a redirect or auth challenge still wins over the value the request went out with.
 * These hold on both the vulnerable and the fixed build; a fix that disables or over-restricts the
 * feature breaks at least one of them.
 */
public class FunctionalTests {

    private static final int T = 30;

    @Test
    void storeCookieIsDeliveredWhenTheCallerSetsNoHeader() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/seed").execute().get(T, TimeUnit.SECONDS);
            c.prepareGet(srv.base() + "/first").execute().get(T, TimeUnit.SECONDS);
            String got = srv.lastCookie("/first");
            assertNotNull(got, "no request reached the server");
            assertTrue(got.contains("SID=storeval"), "the cookie store no longer sends its cookies: " + got);
        }
    }

    @Test
    void aRequestListCookieIsDelivered() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/first").addCookie(new DefaultCookie("a", "1"))
                    .execute().get(T, TimeUnit.SECONDS);
            String got = srv.lastCookie("/first");
            assertNotNull(got, "no request reached the server");
            assertTrue(got.contains("a=1"), "a request cookie was not sent: " + got);
        }
    }

    @Test
    void aCallerHeaderIsDeliveredVerbatimWhenNoStoreCookieCompetes() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/first").setHeader("Cookie", "only=1")
                    .execute().get(T, TimeUnit.SECONDS);
            assertEquals("only=1", srv.lastCookie("/first"), "the caller's header was altered");
        }
    }

    @Test
    void aSessionTheServerRotatesOnARedirectWins() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config().setFollowRedirect(true))) {
            c.prepareGet(srv.base() + "/rotate-redirect").setHeader("Cookie", "SID=old")
                    .execute().get(T, TimeUnit.SECONDS);
            String got = srv.lastCookie("/landing");
            assertNotNull(got, "the redirect target received no request");
            assertTrue(got.contains("SID=rotated"), "the rotated session was not sent: " + got);
            assertFalse(got.contains("SID=old"), "a stale session was sent after rotation: " + got);
        }
    }

    @Test
    void aSessionTheServerRotatesOnAnAuthChallengeWins() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/rotate-auth")
                    .setRealm(basicAuthRealm("user", "pass").setUsePreemptiveAuth(false))
                    .setHeader("Cookie", "SID=old")
                    .execute().get(T, TimeUnit.SECONDS);
            List<String> seen = srv.cookies("/rotate-auth");
            assertEquals(2, seen.size(), "expected an initial 401 and one authenticated retry: " + seen);
            String retry = seen.get(seen.size() - 1);
            assertTrue(retry.contains("SID=rotated"), "the rotated session was not sent on the retry: " + retry);
        }
    }

    @Test
    void theStoreCookieIsStillDeliveredAlongsideACallerHeader() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/seed-multi").execute().get(T, TimeUnit.SECONDS); // SID=storeval, tracking=xyz
            c.prepareGet(srv.base() + "/first").setHeader("Cookie", "session=mine")
                    .execute().get(T, TimeUnit.SECONDS);
            String got = srv.lastCookie("/first");
            assertNotNull(got, "no request reached the server");
            assertTrue(got.contains("tracking=xyz"), "the store's cookie was dropped: " + got);
        }
    }
}
