package htests;

import java.util.Set;

import javax.servlet.Servlet;
import javax.servlet.ServletContainerInitializer;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.ServletRegistration;
import javax.servlet.HttpConstraintElement;
import javax.servlet.ServletSecurityElement;
import javax.servlet.annotation.HttpConstraint;
import javax.servlet.annotation.ServletSecurity.EmptyRoleSemantic;
import javax.servlet.annotation.ServletSecurity.TransportGuarantee;

import org.apache.catalina.Context;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** Rules set through the registration API must cover every mapping the servlet ends up with. */
public class SecMappingTests {

    private Harness h;

    @Before
    public void setUp() throws Exception {
        h = new Harness();
    }

    @After
    public void tearDown() {
        if (h != null) h.close();
    }

    private static ServletSecurityElement denyAll() {
        return new ServletSecurityElement(new HttpConstraintElement(EmptyRoleSemantic.DENY));
    }

    private static ServletSecurityElement adminOnly() {
        return new ServletSecurityElement(new HttpConstraintElement(TransportGuarantee.NONE, "admin"));
    }

    private static ServletContainerInitializer register(final ServletSecurityElement element,
            final boolean securityFirst, final String... patterns) {
        return new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                ServletRegistration.Dynamic r = ctx.addServlet("plain", new PlainServlet());
                if (securityFirst) {
                    r.setServletSecurity(element);
                    for (int i = 0; i < patterns.length; i++) r.addMapping(patterns[i]);
                } else {
                    for (int i = 0; i < patterns.length; i++) r.addMapping(patterns[i]);
                    r.setServletSecurity(element);
                }
            }
        };
    }

    @Test
    public void patternAddedAfterTheRulesIsStillProtected() throws Exception {
        Context ctx = h.webapp(Harness.webXml(""), null);
        h.initializer(ctx, register(denyAll(), true, "/admin/*"));
        h.start();

        Harness.Resp r = h.get("/admin/item");
        assertTrue("a mapping added after the rules must be protected: " + r, r.clientError());
        assertFalse("the servlet must not run: " + r, r.reached());
    }

    @Test
    public void everyAddedPatternIsProtected() throws Exception {
        Context ctx = h.webapp(Harness.webXml(""), null);
        h.initializer(ctx, register(denyAll(), true, "/first/*", "/second/*"));
        h.start();

        Harness.Resp a = h.get("/first/item");
        assertTrue("first mapping must be protected: " + a, a.clientError());
        assertFalse("servlet must not run on the first mapping: " + a, a.reached());
        Harness.Resp b = h.get("/second/item");
        assertTrue("second mapping must be protected: " + b, b.clientError());
        assertFalse("servlet must not run on the second mapping: " + b, b.reached());
    }

    @Test
    public void patternPresentWhenRulesAreSetIsProtected() throws Exception {
        Context ctx = h.webapp(Harness.webXml(""), null);
        h.initializer(ctx, register(denyAll(), false, "/later/*"));
        h.start();

        Harness.Resp r = h.get("/later/item");
        assertTrue("an existing mapping must be protected: " + r, r.clientError());
        assertFalse("the servlet must not run: " + r, r.reached());
    }

    @Test
    public void embeddedContextPatternAddedAfterRulesIsProtected() throws Exception {
        Context ctx = h.embedded();
        h.initializer(ctx, register(denyAll(), true, "/admin/*"));
        h.start();

        Harness.Resp r = h.get("/admin/item");
        assertTrue("a mapping added after the rules must be protected: " + r, r.clientError());
        assertFalse("the servlet must not run: " + r, r.reached());
    }

    @Test
    public void roleRulesAddedAfterMappingDenyClientWithoutTheRole() throws Exception {
        String xml = Harness.webXml(
            "  <login-config><auth-method>BASIC</auth-method></login-config>\n"
          + "  <security-role><role-name>admin</role-name></security-role>\n"
          + "  <security-role><role-name>user</role-name></security-role>\n");
        Context ctx = h.webapp(xml, null);
        h.user("alice", "pw");
        h.role("alice", "user");
        h.initializer(ctx, register(adminOnly(), false, "/role/*"));
        h.start();

        Harness.Resp r = h.getWithCredentials("/role/item", "alice", "pw");
        assertTrue("a client without the required role must be refused: " + r, r.clientError());
        assertFalse("the servlet must not run for a client without the role: " + r, r.reached());
    }
}
