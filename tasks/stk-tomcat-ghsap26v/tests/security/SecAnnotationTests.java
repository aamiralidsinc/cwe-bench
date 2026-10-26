package htests;

import java.util.Set;

import javax.servlet.Servlet;
import javax.servlet.ServletContainerInitializer;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.ServletRegistration;

import org.apache.catalina.Context;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** Access rules declared on a programmatically registered servlet must be enforced. */
public class SecAnnotationTests {

    private Harness h;

    @Before
    public void setUp() throws Exception {
        h = new Harness();
    }

    @After
    public void tearDown() {
        if (h != null) h.close();
    }

    private static ServletContainerInitializer denyAt(final String pattern) {
        return new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                Servlet servlet = ctx.createServlet(DenyServlet.class);
                ServletRegistration.Dynamic r = ctx.addServlet("deny", servlet);
                r.addMapping(pattern);
            }
        };
    }

    @Test
    public void createServletInWebappIsDenied() throws Exception {
        Context ctx = h.webapp(Harness.webXml(""), null);
        h.initializer(ctx, denyAt("/protected"));
        h.start();

        Harness.Resp r = h.get("/protected");
        assertTrue("a request that violates the declared rules must be refused: " + r, r.clientError());
        assertFalse("the servlet must not run: " + r, r.reached());
    }

    @Test
    public void createServletInEmbeddedContextIsDenied() throws Exception {
        Context ctx = h.embedded();
        h.initializer(ctx, denyAt("/protected"));
        h.start();

        Harness.Resp r = h.get("/protected");
        assertTrue("a request that violates the declared rules must be refused: " + r, r.clientError());
        assertFalse("the servlet must not run: " + r, r.reached());
    }

    @Test
    public void descriptorDeclaredServletAnnotationIsDenied() throws Exception {
        String xml = Harness.webXml(
            "  <servlet><servlet-name>d</servlet-name><servlet-class>htests.DenyServlet</servlet-class></servlet>\n"
          + "  <servlet-mapping><servlet-name>d</servlet-name><url-pattern>/ann</url-pattern></servlet-mapping>\n");
        h.webapp(xml, null);
        h.start();

        Harness.Resp r = h.get("/ann");
        assertTrue("a request that violates the declared rules must be refused: " + r, r.clientError());
        assertFalse("the servlet must not run: " + r, r.reached());
    }

    @Test
    public void roleAnnotationDeniesClientWithoutTheRole() throws Exception {
        String xml = Harness.webXml(
            "  <login-config><auth-method>BASIC</auth-method></login-config>\n"
          + "  <security-role><role-name>admin</role-name></security-role>\n"
          + "  <security-role><role-name>user</role-name></security-role>\n");
        Context ctx = h.webapp(xml, null);
        h.user("alice", "pw");
        h.role("alice", "user");
        h.initializer(ctx, new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                Servlet servlet = ctx.createServlet(RoleAdminServlet.class);
                ctx.addServlet("role", servlet).addMapping("/role/*");
            }
        });
        h.start();

        Harness.Resp wrongRole = h.getWithCredentials("/role/item", "alice", "pw");
        assertTrue("a client without the required role must be refused: " + wrongRole, wrongRole.clientError());
        assertFalse("the servlet must not run for a client without the role: " + wrongRole, wrongRole.reached());

        Harness.Resp anonymous = h.get("/role/item");
        assertTrue("an unauthenticated request must be refused: " + anonymous, anonymous.clientError());
        assertFalse("the servlet must not run for an unauthenticated client: " + anonymous, anonymous.reached());
    }

    @Test
    public void methodConstraintDeniesTheCoveredMethod() throws Exception {
        Context ctx = h.webapp(Harness.webXml(""), null);
        h.initializer(ctx, new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                Servlet servlet = ctx.createServlet(MethodServlet.class);
                ctx.addServlet("method", servlet).addMapping("/method/*");
            }
        });
        h.start();

        Harness.Resp r = h.get("/method/item");
        assertTrue("a method that the declared rules deny must be refused: " + r, r.clientError());
        assertFalse("the servlet must not run for a denied method: " + r, r.reached());
    }
}
