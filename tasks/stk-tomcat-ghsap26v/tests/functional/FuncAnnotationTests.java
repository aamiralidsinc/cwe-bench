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

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/** Legitimate annotation-declared access must keep working. */
public class FuncAnnotationTests {

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
    public void permitAnnotationKeepsTheServletReachable() throws Exception {
        Context ctx = h.webapp(Harness.webXml(""), null);
        h.initializer(ctx, new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                Servlet servlet = ctx.createServlet(PermitServlet.class);
                ctx.addServlet("open", servlet).addMapping("/open/*");
            }
        });
        h.start();

        Harness.Resp r = h.get("/open/item");
        assertEquals("a permit rule must keep the servlet reachable", 200, r.code);
        assertTrue("the servlet must run: " + r, r.reached());
    }

    @Test
    public void plainServletStaysReachable() throws Exception {
        Context ctx = h.webapp(Harness.webXml(""), null);
        h.initializer(ctx, new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                ctx.addServlet("plain", new PlainServlet()).addMapping("/plain/*");
            }
        });
        h.start();

        Harness.Resp r = h.get("/plain/item");
        assertEquals("a servlet with no access rules must stay reachable", 200, r.code);
        assertTrue("the servlet must run: " + r, r.reached());
    }

    @Test
    public void descriptorRuleWinsOverAPermitAnnotation() throws Exception {
        String xml = Harness.webXml(
            "  <servlet><servlet-name>p</servlet-name><servlet-class>htests.PermitServlet</servlet-class></servlet>\n"
          + "  <servlet-mapping><servlet-name>p</servlet-name><url-pattern>/locked</url-pattern></servlet-mapping>\n"
          + "  <security-constraint>\n"
          + "    <web-resource-collection><url-pattern>/locked</url-pattern></web-resource-collection>\n"
          + "    <auth-constraint/>\n"
          + "  </security-constraint>\n");
        h.webapp(xml, null);
        h.start();

        Harness.Resp r = h.get("/locked");
        assertTrue("a deployment-descriptor rule must keep priority: " + r, r.clientError());
    }

    @Test
    public void rulesForOneServletDoNotAffectAnother() throws Exception {
        String xml = Harness.webXml(
            "  <servlet><servlet-name>free</servlet-name><servlet-class>htests.PlainServlet</servlet-class></servlet>\n"
          + "  <servlet-mapping><servlet-name>free</servlet-name><url-pattern>/free</url-pattern></servlet-mapping>\n");
        Context ctx = h.webapp(xml, null);
        h.initializer(ctx, new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                Servlet servlet = ctx.createServlet(DenyServlet.class);
                ctx.addServlet("denied", servlet).addMapping("/denied");
            }
        });
        h.start();

        // Touch the annotated servlet first so its rules are processed, then check the other one.
        h.get("/denied");
        Harness.Resp free = h.get("/free");
        assertEquals("another servlet's rules must not change this one", 200, free.code);
        assertTrue("the unconstrained servlet must run: " + free, free.reached());
    }

    @Test
    public void methodConstraintKeepsOtherMethodsWorking() throws Exception {
        Context ctx = h.webapp(Harness.webXml(""), null);
        h.initializer(ctx, new ServletContainerInitializer() {
            public void onStartup(Set<Class<?>> classes, ServletContext ctx) throws ServletException {
                Servlet servlet = ctx.createServlet(MethodServlet.class);
                ctx.addServlet("method", servlet).addMapping("/method/*");
            }
        });
        h.start();

        Harness.Resp r = h.post("/method/item", null, "");
        assertEquals("a method not covered by the deny rule must stay reachable", 200, r.code);
        assertTrue("the servlet must run for the permitted method: " + r, r.reached());
    }
}
