package hudson.security.bt;

import com.gargoylesoftware.htmlunit.FailingHttpStatusCodeException;
import com.gargoylesoftware.htmlunit.Page;
import com.gargoylesoftware.htmlunit.HttpMethod;
import com.gargoylesoftware.htmlunit.WebRequestSettings;
import com.gargoylesoftware.htmlunit.html.HtmlElement;
import com.gargoylesoftware.htmlunit.html.HtmlForm;
import com.gargoylesoftware.htmlunit.html.HtmlInput;
import com.gargoylesoftware.htmlunit.html.HtmlPage;
import hudson.matrix.MatrixProject;
import hudson.model.AbstractProject;
import hudson.model.FreeStyleProject;
import hudson.model.Item;
import hudson.model.Job;
import hudson.model.Result;
import hudson.security.ACL;
import hudson.security.HudsonPrivateSecurityRealm;
import hudson.security.Permission;
import hudson.tasks.BuildTrigger;
import jenkins.model.Jenkins;
import org.acegisecurity.context.SecurityContext;
import org.acegisecurity.context.SecurityContextHolder;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.JenkinsRule.WebClient;
import org.junit.Assert;
import org.junit.Rule;

import java.io.File;
import java.net.URL;
import java.util.Collections;

/**
 * Shared fixture: a real Jenkins controller, a per-job permission matrix, and the
 * product's own HTTP entry points for configuration writes.
 */
public abstract class BtTest {

    protected static final String ATTACKER = "attacker";
    protected static final String ADMIN = "admin";

    @Rule
    public JenkinsRule j = new JenkinsRule();

    protected BtAuthz authz;

    // ------------------------------------------------------------------ fixtures

    protected FreeStyleProject free(String name) throws Exception {
        return j.jenkins.createProject(FreeStyleProject.class, name);
    }

    protected MatrixProject matrix(String name) throws Exception {
        return j.jenkins.createProject(MatrixProject.class, name);
    }

    /** Stores a build-other-projects entry as the controller itself would. */
    protected void storeTrigger(final AbstractProject<?, ?> project, final String children) throws Exception {
        asSystem(new Runnable() {
            public void run() {
                try {
                    project.getPublishersList().replaceBy(
                            Collections.singletonList(new BuildTrigger(children, Result.SUCCESS.toString())));
                    project.save();
                    jenkins.model.Jenkins.getInstance().rebuildDependencyGraph();
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            }
        });
    }

    protected static String storedChildren(AbstractProject<?, ?> project) throws Exception {
        BuildTrigger t = project.getPublishersList().get(BuildTrigger.class);
        return t == null ? null : t.getChildProjectsValue();
    }

    protected String configXml(AbstractProject<?, ?> source) throws Exception {
        return source.getConfigFile().asString();
    }

    /** Enables a real security realm and a per-job permission matrix. */
    protected void enableAcl() throws Exception {
        // A named realm the controller can serialise, unlike the harness's anonymous
        // test realm: a refusal path that rolls a half-created item back saves the
        // controller's configuration, and that must not fail for fixture reasons.
        HudsonPrivateSecurityRealm realm = new HudsonPrivateSecurityRealm(false, false, null);
        realm.createAccount(ATTACKER, ATTACKER);
        realm.createAccount(ADMIN, ADMIN);
        j.jenkins.setSecurityRealm(realm);
        j.jenkins.setCrumbIssuer(null);
        authz = new BtAuthz();
        authz.grant(ADMIN, Jenkins.ADMINISTER);
        authz.grant(ATTACKER, Jenkins.READ, Job.CREATE);
        j.jenkins.setAuthorizationStrategy(authz);
    }

    protected void grant(Job<?, ?> job, String user, Permission... perms) throws Exception {
        authz.grant(job, user, perms);
    }

    protected void grantRoot(String user, Permission... perms) {
        authz.grant(user, perms);
    }

    protected static void asSystem(Runnable r) {
        SecurityContext orig = ACL.impersonate(ACL.SYSTEM);
        try {
            r.run();
        } finally {
            SecurityContextHolder.setContext(orig);
        }
    }

    // ------------------------------------------------------------------ HTTP entry points

    protected WebClient client(String user) throws Exception {
        WebClient wc = j.createWebClient();
        wc.setThrowExceptionOnFailingStatusCode(false);
        wc.setRedirectEnabled(false);
        HtmlPage login = (HtmlPage) wc.getPage(j.getURL() + "login");
        HtmlForm form = login.getFormByName("login");
        form.getInputByName("j_username").setValueAttribute(user);
        form.getInputByName("j_password").setValueAttribute(user);
        form.submit(null);
        return wc;
    }

    /** POST the configuration page form, changing the build-other-projects field. */
    protected int submitConfigForm(AbstractProject<?, ?> project, String user, String children)
            throws Exception {
        WebClient wc = client(user);
        HtmlPage cfg = wc.getPage(project, "configure");
        HtmlForm form = cfg.getFormByName("config");
        HtmlInput field = null;
        for (HtmlElement e : form.getElementsByTagName("input")) {
            if (!(e instanceof HtmlInput)) {
                continue;
            }
            String name = ((HtmlInput) e).getNameAttribute();
            if (!"buildTrigger.childProjects".equals(name) && !"childProjects".equals(name)
                    && !name.endsWith(".childProjects")) {
                continue;
            }
            if (insidePrototype(e)) {
                continue;
            }
            field = (HtmlInput) e;
            break;
        }
        Assert.assertNotNull("the configuration page has no build-other-projects field", field);
        field.setValueAttribute(children);
        HtmlElement save = null;
        for (HtmlElement e : form.getElementsByTagName("button")) {
            if (e.asText().trim().equals("Save")) {
                save = e;
                break;
            }
        }
        Assert.assertNotNull("the configuration page has no save control", save);
        try {
            Page after = form.submit((com.gargoylesoftware.htmlunit.html.SubmittableElement) save);
            return after.getWebResponse().getStatusCode();
        } catch (FailingHttpStatusCodeException e) {
            return e.getStatusCode();
        }
    }

    private static boolean insidePrototype(HtmlElement e) {
        for (HtmlElement p = e; p != null; p = p.getParentNode() instanceof HtmlElement
                ? (HtmlElement) p.getParentNode() : null) {
            String cls = p.getAttribute("class");
            if (cls != null && cls.contains("prototypes")) {
                return true;
            }
        }
        return false;
    }

    protected WebRequestSettings request(String path, HttpMethod method) throws Exception {
        return new WebRequestSettings(new URL(j.getURL(), path), method);
    }

    protected int postXml(String path, String xml, String user) throws Exception {
        WebClient wc = client(user);
        WebRequestSettings req = request(path, HttpMethod.POST);
        req.setAdditionalHeader("Content-Type", "application/xml");
        req.setRequestBody(xml);
        try {
            Page p = wc.getPage(req);
            return p.getWebResponse().getStatusCode();
        } catch (FailingHttpStatusCodeException e) {
            return e.getStatusCode();
        }
    }

    protected int post(String path, String body, String contentType, String user) throws Exception {
        WebClient wc = client(user);
        WebRequestSettings req = request(path, HttpMethod.POST);
        if (contentType != null) {
            req.setAdditionalHeader("Content-Type", contentType);
        }
        if (body != null) {
            req.setRequestBody(body);
        }
        try {
            Page p = wc.getPage(req);
            return p.getWebResponse().getStatusCode();
        } catch (FailingHttpStatusCodeException e) {
            return e.getStatusCode();
        }
    }

    // ------------------------------------------------------------------ assertions

    protected static void assertClientError(int status) {
        Assert.assertTrue("expected a client error refusal, got " + status,
                status >= 400 && status < 500);
    }

    protected static void assertSuccess(int status) {
        Assert.assertTrue("expected the change to be accepted, got " + status,
                status >= 200 && status < 400);
    }

    protected static File jobDir(Jenkins jenkins, String name) {
        return new File(new File(jenkins.getRootDir(), "jobs"), name);
    }
}
