package htests;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/** The ordinary form-login flow and descriptor-declared rules must keep working. */
public class FuncFormLoginTests {

    private Harness h;

    @Before
    public void setUp() throws Exception {
        h = new Harness();
    }

    @After
    public void tearDown() {
        if (h != null) h.close();
    }

    @Test
    public void loginReachesTheProtectedResource() throws Exception {
        h.user("bob", "pw");
        h.role("bob", "admin");
        h.role("bob", "user");
        h.webapp(Fixtures.formApp(), Fixtures.formFiles());
        h.start();

        String cookie = Forms.login(h, "bob", "pw");
        Harness.Resp r = h.get("/app/protected", cookie);
        assertEquals("a logged-in client with the required role must reach the resource", 200, r.code);
        assertTrue("the protected servlet must run: " + r, r.reached());
    }

    @Test
    public void loginDoesNotGrantARoleTheClientLacks() throws Exception {
        h.user("alice", "pw");
        h.role("alice", "user");
        h.webapp(Fixtures.formApp(), Fixtures.formFiles());
        h.start();

        String cookie = Forms.login(h, "alice", "pw");
        Harness.Resp r = h.get("/app/admin", cookie);
        assertTrue("a logged-in client without the role must be refused: " + r, r.clientError());
    }

    @Test
    public void descriptorRuleIsEnforcedWithoutALoginConfiguration() throws Exception {
        h.webapp(Fixtures.metadataCompleteApp(), null);
        h.start();

        Harness.Resp r = h.get("/protected");
        assertTrue("a descriptor rule must stay enforced: " + r, r.clientError());
    }

    @Test
    public void loginPageIsReachable() throws Exception {
        h.webapp(Fixtures.formApp(), Fixtures.formFiles());
        h.start();

        Harness.Resp r = h.get("/login.html");
        assertEquals("the login page must stay reachable", 200, r.code);
    }
}
