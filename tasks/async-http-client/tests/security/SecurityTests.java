import org.asynchttpclient.*;
import io.netty.handler.codec.http.cookie.DefaultCookie;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.asynchttpclient.Dsl.*;
import static org.junit.jupiter.api.Assertions.*;

/**
 * The attack: a client with its default cookie store already holds a session cookie for an origin
 * (seeded here by a prior Set-Cookie response). A request the caller builds with its own Cookie
 * request header must reach the server carrying the caller's cookie, not the stored one. Each test
 * asserts the attack is BLOCKED (the caller's cookie is what the server receives). On the vulnerable
 * build the stored cookie silently replaces the caller's, so each test fails there.
 */
public class SecurityTests {

    private static final int T = 30;

    @Test
    void callerCookieHeaderNotReplacedByStoreOnFirstRequest() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/seed").execute().get(T, TimeUnit.SECONDS); // store: SID=storeval
            c.prepareGet(srv.base() + "/first").setHeader("Cookie", "SID=userB")
                    .execute().get(T, TimeUnit.SECONDS);
            String got = srv.lastCookie("/first");
            assertNotNull(got, "no request reached the server");
            assertTrue(got.contains("SID=userB"), "caller's cookie was not sent: " + got);
            assertFalse(got.contains("storeval"), "the stored session was sent instead of the caller's: " + got);
        }
    }

    @Test
    void callerCookieHeaderNotDroppedWhenStoreHoldsADifferentCookie() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/seed-multi").execute().get(T, TimeUnit.SECONDS); // SID=storeval, tracking=xyz
            c.prepareGet(srv.base() + "/first").setHeader("Cookie", "session=mine")
                    .execute().get(T, TimeUnit.SECONDS);
            String got = srv.lastCookie("/first");
            assertNotNull(got, "no request reached the server");
            assertTrue(got.contains("session=mine"), "caller's cookie was dropped by the store: " + got);
        }
    }

    @Test
    void callerCookieHeaderHonoredAcrossARedirect() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config().setFollowRedirect(true))) {
            c.prepareGet(srv.base() + "/seed").execute().get(T, TimeUnit.SECONDS);
            c.prepareGet(srv.base() + "/redirect").setHeader("Cookie", "SID=userB")
                    .execute().get(T, TimeUnit.SECONDS);
            String got = srv.lastCookie("/landing");
            assertNotNull(got, "the redirect target received no request");
            assertTrue(got.contains("SID=userB"), "the follow-up request carried the stored session, not the caller's: " + got);
            assertFalse(got.contains("storeval"), "the stored session leaked on the redirect hop: " + got);
        }
    }

    @Test
    void callerCookieHeaderHonoredOnAnAuthenticationRetry() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/seed").execute().get(T, TimeUnit.SECONDS);
            c.prepareGet(srv.base() + "/auth")
                    .setRealm(basicAuthRealm("user", "pass").setUsePreemptiveAuth(false))
                    .setHeader("Cookie", "SID=userB")
                    .execute().get(T, TimeUnit.SECONDS);
            List<String> seen = srv.cookies("/auth");
            assertEquals(2, seen.size(), "expected an initial 401 and one authenticated retry: " + seen);
            String retry = seen.get(seen.size() - 1);
            assertTrue(retry.contains("SID=userB"), "the authenticated retry carried the stored session, not the caller's: " + retry);
            assertFalse(retry.contains("storeval"), "the stored session leaked on the auth retry: " + retry);
        }
    }

    @Test
    void multipleCallerCookieHeadersAreNotReplacedByTheStore() throws Exception {
        try (StubServer srv = new StubServer();
             AsyncHttpClient c = asyncHttpClient(config())) {
            c.prepareGet(srv.base() + "/seed").execute().get(T, TimeUnit.SECONDS); // SID=storeval
            c.prepareGet(srv.base() + "/first")
                    .addHeader("Cookie", "a=1").addHeader("Cookie", "b=2")
                    .execute().get(T, TimeUnit.SECONDS);
            String got = srv.lastCookie("/first");
            assertNotNull(got, "no request reached the server");
            assertTrue(got.contains("a=1") && got.contains("b=2"),
                    "the caller's cookies were replaced by the stored session: " + got);
        }
    }
}
