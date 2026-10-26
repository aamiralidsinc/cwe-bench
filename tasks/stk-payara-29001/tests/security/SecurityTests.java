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

    // ---- the response representation is the content provider's choice

    @Test
    public void responseTypeIsNotTakenFromTheRequestLogViewer() throws Exception {
        try (Sink admin = new Sink()) {
            Req req = new Req("LogViewer").param("start", "0").param("instanceName", "server")
                .param("restUrl", admin.adminBase).session("REST_URL", admin.adminBase).param("ContentType", "text/html");
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "log viewer download");
            if (ok(r)) {
                assertFalse("text/html".equalsIgnoreCase(r.responseHeader("Content-type")),
                    "the response Content-Type was taken from the request: " + r.responseHeader("Content-type"));
            }
        }
    }

    @Test
    public void responseTypeIsNotTakenFromTheRequestLogFiles() throws Exception {
        try (Sink admin = new Sink()) {
            Req req = new Req("LogFiles").param("target", "server").param("restUrl", admin.adminBase)
                .session("REST_URL", admin.adminBase).param("ContentType", "application/xhtml+xml");
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "log-file download");
            if (ok(r)) {
                assertFalse("application/xhtml+xml".equalsIgnoreCase(r.responseHeader("Content-type")),
                    "the response Content-Type was taken from the request: " + r.responseHeader("Content-type"));
            }
        }
    }

    // ---- a request-supplied name may not address another resource or location

    @Test
    public void stagingLocationIsNotChosenByTheLogTarget() throws Exception {
        try (Sink admin = new Sink()) {
            Req req = new Req("LogFiles").param("target", Harness.unique("x/../../payara-canary"))
                .param("restUrl", admin.adminBase).session("REST_URL", admin.adminBase);
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "log-file download");
            if (ok(r)) {
                Rec rec = admin.first("/collect-log-files");
                assertNotNull(rec, "expected the console to use its own admin endpoint");
                String id = rec.form().get("id");
                assertTrue(Harness.inside(r.staging, id),
                    "the console asked the admin server to write outside its staging directory: " + id);
            }
        }
    }

    @Test
    public void resourcePathIsNotChosenByTheApplicationName() throws Exception {
        try (Sink admin = new Sink()) {
            Req req = new Req("ClientStubs").param("appName", "x/../../domain")
                .param("restUrl", admin.adminBase).session("REST_URL", admin.adminBase);
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "client-stub download");
            if (ok(r)) {
                Rec rec = admin.first("/get-client-stubs");
                assertNotNull(rec, "expected the console to use its own admin endpoint");
                assertTrue(rec.rawPath.matches(".*/applications/application/[^/]+/get-client-stubs"),
                    "the application name changed the admin resource path: " + rec.rawPath);
            }
        }
    }

    @Test
    public void stagingLocationIsNotChosenByTheApplicationName() throws Exception {
        try (Sink admin = new Sink()) {
            Req req = new Req("ClientStubs").param("appName", Harness.unique("x/../../payara-canary"))
                .param("restUrl", admin.adminBase).session("REST_URL", admin.adminBase);
            Result r = Harness.dispatch(req.sameOrigin());
            notCrashed(r, "client-stub download");
            if (ok(r)) {
                Rec rec = admin.first("/get-client-stubs");
                assertNotNull(rec, "expected the console to use its own admin endpoint");
                String localDir = rec.query("localDir");
                assertTrue(Harness.inside(r.staging, localDir),
                    "the console asked the admin server to write outside its staging directory: " + localDir);
            }
        }
    }
}
