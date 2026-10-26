package htests;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * A servlet whose path merely ends with the form login action name is still a servlet: its
 * declared role rules apply. The ordinary login flow is exercised first so the request carries
 * a real authenticated session.
 */
public class SecFormActionTests {

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
    public void servletUnderTheLoginActionNameRequiresItsRole() throws Exception {
        h.user("alice", "pw");
        h.role("alice", "user");
        h.webapp(Fixtures.formApp(), Fixtures.formFiles());
        h.start();

        String cookie = Forms.login(h, "alice", "pw");
        Harness.Resp allowed = h.get("/app/protected", cookie);
        assertEquals("the ordinary protected resource must stay reachable", 200, allowed.code);
        assertTrue("the ordinary protected resource must run its servlet: " + allowed, allowed.reached());

        Harness.Resp r = h.get("/app/j_security_check", cookie);
        assertTrue("a servlet under the login action name must enforce its role rules: " + r, r.clientError());
        assertFalse("the servlet must not run for a client without the role: " + r, r.reached());
    }
}
