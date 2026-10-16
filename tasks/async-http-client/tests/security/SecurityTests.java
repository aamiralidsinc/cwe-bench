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

    /**
     * The caller names SID with a value that is not strict RFC 6265 cookie syntax (real servers issue
     * such values), next to an ordinary pair. Whatever the client does with the unusual value, it must
     * never send the store's SID (another user's session) in its place, because the caller named SID.
     * Delivering the caller's header and refusing the request are both acceptable here; substituting
     * the stored session is not. When a request does go out, the caller's ordinary pair must be in it.
     */
    @Test
    void storedSessionNotSubstitutedForANamedCallerCookieWithAnUnusualValue() throws Exception {
        for (String sid : new String[] {"user\"B", "user B"}) {
            String header = "SID=" + sid + "; x=1";
            try (StubServer srv = new StubServer();
                 AsyncHttpClient c = asyncHttpClient(config())) {
                c.prepareGet(srv.base() + "/seed").execute().get(T, TimeUnit.SECONDS); // store: SID=storeval
                try {
                    c.prepareGet(srv.base() + "/first").setHeader("Cookie", header)
                            .execute().get(T, TimeUnit.SECONDS);
                } catch (Exception refused) {
                    // A client may refuse a header it considers malformed; the leak check below still applies.
                }
                for (String got : srv.cookies("/first")) {
                    assertFalse(got.contains("storeval"),
                            "caller set [" + header + "] but the stored session was sent: " + got);
                    assertTrue(got.contains("x=1"),
                            "caller set [" + header + "] but its ordinary pair was not delivered: " + got);
                }
            }
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
