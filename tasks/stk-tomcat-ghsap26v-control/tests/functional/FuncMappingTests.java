package htests;

import java.util.Set;

import javax.servlet.ServletContainerInitializer;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.ServletRegistration;
import javax.servlet.HttpConstraintElement;
import javax.servlet.ServletSecurityElement;
import javax.servlet.annotation.HttpConstraint;
import javax.servlet.annotation.ServletSecurity.TransportGuarantee;

import org.apache.catalina.Context;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/** Legitimate registration and role rules must keep working. */
public class FuncMappingTests {

    private Harness h;

    @Before
    public void setUp() throws Exception {
        h = new Harness();
    }

    @After
    public void tearDown() {
        if (h != null) h.close();
    }

    private static ServletSecurityElement adminOnly() {
        return new ServletSecurityElement(new HttpConstraintElement(TransportGuarantee.NONE, "admin"));
    }

    @Test
    public void authorizedClientReachesTheServlet() throws Exception {
        String xml = Harness.webXml(
            "  <login-config><auth-method>BASIC</auth-method></login-config>\n"
          + "  <security-role><role-name>admin</role-name></security-role>\n"
          + "  <security-role><role-name>user</role-name></security-role>\n");
        Context ctx = h.webapp(xml, null);
        h.user("bob", "pw");
        h.role("bob", "admin");
        h.initializer(ctx, new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                ServletRegistration.Dynamic r = ctx.addServlet("plain", new PlainServlet());
                r.setServletSecurity(adminOnly());
                r.addMapping("/role/*");
            }
        });
        h.start();

        Harness.Resp r = h.getWithCredentials("/role/item", "bob", "pw");
        assertEquals("a client with the required role must reach the servlet", 200, r.code);
        assertTrue("the servlet must run: " + r, r.reached());
    }

    @Test
    public void unconstrainedServletIsUnaffected() throws Exception {
        String xml = Harness.webXml(
            "  <servlet><servlet-name>locked</servlet-name><servlet-class>htests.PlainServlet</servlet-class></servlet>\n"
          + "  <servlet><servlet-name>free</servlet-name><servlet-class>htests.PlainServlet</servlet-class></servlet>\n"
          + "  <servlet-mapping><servlet-name>locked</servlet-name><url-pattern>/locked</url-pattern></servlet-mapping>\n"
          + "  <servlet-mapping><servlet-name>free</servlet-name><url-pattern>/free</url-pattern></servlet-mapping>\n"
          + "  <security-constraint>\n"
          + "    <web-resource-collection><url-pattern>/locked</url-pattern></web-resource-collection>\n"
          + "    <auth-constraint/>\n"
          + "  </security-constraint>\n");
        h.webapp(xml, null);
        h.start();

        Harness.Resp free = h.get("/free");
        assertEquals("an unconstrained servlet must stay reachable", 200, free.code);
        assertTrue("the unconstrained servlet must run: " + free, free.reached());
        Harness.Resp locked = h.get("/locked");
        assertTrue("the constrained servlet must stay protected: " + locked, locked.clientError());
    }

    @Test
    public void authorizedClientReachesServletsWhoseRulesCameAfterMapping() throws Exception {
        String xml = Harness.webXml(
            "  <login-config><auth-method>BASIC</auth-method></login-config>\n"
          + "  <security-role><role-name>admin</role-name></security-role>\n");
        Context ctx = h.webapp(xml, null);
        h.user("bob", "pw");
        h.role("bob", "admin");
        h.initializer(ctx, new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                ServletRegistration.Dynamic r = ctx.addServlet("plain", new PlainServlet());
                r.addMapping("/late/*");
                r.setServletSecurity(adminOnly());
            }
        });
        h.start();

        Harness.Resp r = h.getWithCredentials("/late/item", "bob", "pw");
        assertEquals("a client with the required role must reach the servlet", 200, r.code);
        assertTrue("the servlet must run: " + r, r.reached());
    }
}
