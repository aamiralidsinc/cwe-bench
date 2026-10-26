package functional;

import harness.Harness;
import harness.Harness.Rec;
import harness.Harness.Req;
import harness.Harness.Result;
import harness.Harness.Sink;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Legitimate console downloads that must keep working exactly as today. */
public class FunctionalTests {

    private static Result firstWorking(Req base, Sink admin) {
        Req withHint = base.copy().param("restUrl", admin.adminBase).session("REST_URL", admin.adminBase);
        Result r = Harness.dispatch(withHint.sameOrigin());
        if (r.status >= 200 && r.status < 300) return r;
        return Harness.dispatch(base.copy().session("REST_URL", admin.adminBase).sameOrigin());
    }

    private static void ok(Result r, String what) {
        assertTrue(r.status >= 200 && r.status < 300,
            what + " failed with status " + r.status + (r.thrown == null ? "" : ": " + r.thrown));
    }

    private static Rec expectTokenAtConsole(Sink admin, String suffix) {
        Rec rec = admin.first(suffix);
        assertNotNull(rec, "the console never called its own admin endpoint " + suffix);
        assertTrue(rec.carriesToken(Harness.TOKEN_VALUE),
            "the console did not authenticate to its own admin endpoint");
        return rec;
    }

    @Test
    public void logFileDownloadStillWorks() throws Exception {
        try (Sink admin = new Sink()) {
            Result r = firstWorking(new Req("LogFiles").param("target", "server"), admin);
            ok(r, "log-file download");
            assertArrayEquals(Harness.ZIP_BYTES, r.body, "the download body changed");
            Rec rec = expectTokenAtConsole(admin, "/collect-log-files");
            assertTrue(Harness.inside(r.staging, rec.form().get("id")),
                "the staged file left the console staging directory");
            assertEquals("application/octet-stream", r.responseHeader("Content-type"));
        }
    }

    @Test
    public void logViewerDownloadStillWorks() throws Exception {
        try (Sink admin = new Sink()) {
            Result r = firstWorking(new Req("LogViewer").param("start", "0").param("instanceName", "server"), admin);
            ok(r, "log viewer download");
            assertEquals(Harness.LOG_BODY, r.bodyText(), "the log body changed");
            assertEquals("next-1", r.responseHeader("X-Text-Append-Next"), "the log paging header was lost");
            assertEquals("text/plain", r.responseHeader("Content-type"));
            expectTokenAtConsole(admin, "/view-log/");
        }
    }

    @Test
    public void clientStubDownloadStillWorks() throws Exception {
        try (Sink admin = new Sink()) {
            Result r = firstWorking(new Req("ClientStubs").param("appName", "my-app"), admin);
            ok(r, "client-stub download");
            assertArrayEquals(Harness.ZIP_BYTES, r.body, "the download body changed");
            Rec rec = expectTokenAtConsole(admin, "/get-client-stubs");
            assertTrue(Harness.inside(r.staging, rec.query("localDir")),
                "the staged file left the console staging directory");
            assertEquals("application/octet-stream", r.responseHeader("Content-type"));
        }
    }

    @Test
    public void namesThatAreLegalTodayKeepWorking() throws Exception {
        try (Sink admin = new Sink()) {
            Result stubs = firstWorking(new Req("ClientStubs").param("appName", "my-app_1.2"), admin);
            ok(stubs, "client-stub download for a legal application name");
            assertArrayEquals(Harness.ZIP_BYTES, stubs.body);
            Rec srec = expectTokenAtConsole(admin, "/get-client-stubs");
            assertTrue(srec.rawPath.contains("/applications/application/my-app_1.2/get-client-stubs"),
                "the application name was not preserved in the resource path: " + srec.rawPath);

            Result logs = firstWorking(new Req("LogFiles").param("target", "node-1.prod"), admin);
            ok(logs, "log-file download for a legal target name");
            assertArrayEquals(Harness.ZIP_BYTES, logs.body);
            Rec lrec = expectTokenAtConsole(admin, "/collect-log-files");
            assertTrue(lrec.form().get("target").equals("node-1.prod"),
                "the target name was not preserved");
            assertTrue(Harness.inside(logs.staging, lrec.form().get("id")),
                "the staged file left the console staging directory");
        }
    }

    @Test
    public void unrelatedRequestParametersDoNotBreakDownloads() throws Exception {
        try (Sink admin = new Sink()) {
            Result r = firstWorking(new Req("LogFiles").param("target", "server").param("unrelated", "value"), admin);
            ok(r, "log-file download with an unrelated parameter");
            assertArrayEquals(Harness.ZIP_BYTES, r.body);
        }
    }

    @Test
    public void projectRestResponseTestStillPasses() throws Exception {
        Class<?> c = Class.forName("org.glassfish.admingui.common.test.RestResponseTest");
        org.junit.runner.Result result = org.junit.runner.JUnitCore.runClasses(c);
        assertTrue(result.wasSuccessful(), "the project's own REST response test failed: " + result.getFailures());
    }
}
