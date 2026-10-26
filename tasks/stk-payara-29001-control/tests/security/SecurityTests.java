package security;

import harness.Harness;
import harness.Harness.Rec;
import harness.Harness.Req;
import harness.Harness.Result;
import harness.Harness.Sink;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** The attacks that must be refused (or neutralised) at the console download entry point. */
public class SecurityTests {

    private static void notCrashed(Result r, String what) {
        assertFalse(r.serverError(), what + ": server error is not a refusal (status " + r.status
            + (r.thrown == null ? "" : ", " + r.thrown) + ")");
    }

    private static boolean ok(Result r) { return r.status >= 200 && r.status < 300; }

    // ---- the console's stored admin credential must reach only the console's own endpoint

    @Test
    public void storedCredentialNeverGoesToRequestChosenHostLogFiles() throws Exception {
        try (Sink admin = new Sink(); Sink other = new Sink()) {
            Req req = new Req("LogFiles").param("target", "server").param("restUrl", other.adminBase)
                .session("REST_URL", admin.adminBase);
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "log-file download");
            for (Rec rec : other.all()) {
                assertFalse(rec.carriesToken(Harness.TOKEN_VALUE),
                    "the stored admin credential was sent to the request-chosen host: " + rec.rawPath);
            }
        }
    }

    @Test
    public void storedCredentialNeverGoesToRequestChosenHostClientStubs() throws Exception {
        try (Sink admin = new Sink(); Sink other = new Sink()) {
            Req req = new Req("ClientStubs").param("appName", "my-app").param("restUrl", other.adminBase)
                .session("REST_URL", admin.adminBase);
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "client-stub download");
            for (Rec rec : other.all()) {
                assertFalse(rec.carriesToken(Harness.TOKEN_VALUE),
                    "the stored admin credential was sent to the request-chosen host: " + rec.rawPath);
            }
        }
    }

    @Test
    public void storedCredentialNeverGoesToRequestChosenHostLogViewer() throws Exception {
        try (Sink admin = new Sink(); Sink other = new Sink()) {
            Req req = new Req("LogViewer").param("start", "0").param("instanceName", "server")
                .param("restUrl", other.adminBase)
                .session("REST_URL", admin.adminBase);
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "log viewer download");
            for (Rec rec : other.all()) {
                assertFalse(rec.carriesToken(Harness.TOKEN_VALUE),
                    "the stored admin credential was sent to the request-chosen host: " + rec.rawPath);
            }
        }
    }


    @Test
    public void requestChosenHostIsNotContacted() throws Exception {
        try (Sink admin = new Sink(); Sink other = new Sink()) {
            Req req = new Req("LogFiles").param("target", "server").param("restUrl", other.adminBase)
                .session("REST_URL", admin.adminBase);
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "log-file download");
            assertTrue(other.all().isEmpty(),
                "the console contacted the request-chosen host");
        }
    }
}
