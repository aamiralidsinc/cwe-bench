package bench.jch;

import hudson.model.FreeStyleProject;
import hudson.model.Item;
import hudson.model.ParametersDefinitionProperty;
import hudson.model.PasswordParameterDefinition;
import jenkins.model.Jenkins;
import org.htmlunit.HttpMethod;
import org.htmlunit.Page;
import org.htmlunit.WebRequest;
import org.htmlunit.html.HtmlForm;
import org.htmlunit.html.HtmlPage;
import org.junit.Before;
import org.junit.Rule;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.MockAuthorizationStrategy;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * Fixture shared by the behavioural suites: a real Jenkins controller, a per-user permission
 * matrix, a job whose saved revisions contain real encrypted values, and the product's HTTP
 * entry points.
 */
public abstract class BenchBase {

    protected static final String ADMIN = "admin";
    protected static final String READER = "reader";
    protected static final String CONFIGURER = "configurer";

    protected static final String FIRST_SECRET = "first-token-value";
    protected static final String SECOND_SECRET = "second-token-value";
    protected static final String LEGACY_TOKEN = "legacy-plain-token-value";
    protected static final String OLD_DESCRIPTION = "revision-one-marker";
    protected static final String NEW_DESCRIPTION = "revision-two-marker";

    @Rule
    public JenkinsRule j = new JenkinsRule();

    private final Map<String, JenkinsRule.WebClient> clients = new HashMap<String, JenkinsRule.WebClient>();

    @Before
    public void configureSecurity() throws Exception {
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        j.jenkins.setCrumbIssuer(null);
        j.jenkins.setAuthorizationStrategy(new MockAuthorizationStrategy()
                .grant(Jenkins.ADMINISTER).everywhere().to(ADMIN)
                .grant(Jenkins.READ).everywhere().to(READER)
                .grant(Item.READ).everywhere().to(READER)
                .grant(Item.EXTENDED_READ).everywhere().to(READER)
                .grant(Jenkins.READ).everywhere().to(CONFIGURER)
                .grant(Item.READ).everywhere().to(CONFIGURER)
                .grant(Item.CONFIGURE).everywhere().to(CONFIGURER));
    }

    // ------------------------------------------------------------------ HTTP

    protected JenkinsRule.WebClient client(String user) throws Exception {
        JenkinsRule.WebClient cached = clients.get(user);
        if (cached != null) {
            return cached;
        }
        JenkinsRule.WebClient wc = j.createWebClient();
        wc.getOptions().setJavaScriptEnabled(false);
        wc.getOptions().setCssEnabled(false);
        wc.setThrowExceptionOnFailingStatusCode(false);
        wc.setRedirectEnabled(false);
        HtmlPage login = wc.goTo("login");
        HtmlForm form = login.getFormByName("login");
        form.getInputByName("j_username").setValueAttribute(user);
        form.getInputByName("j_password").setValueAttribute(user);
        form.submit(null);
        clients.put(user, wc);
        return wc;
    }

    protected Page get(String path, String user) throws Exception {
        return client(user).getPage(j.getURL() + path);
    }

    protected Page post(String path, String formBody, String user) throws Exception {
        WebRequest request = new WebRequest(new URL(j.getURL(), path), HttpMethod.POST);
        request.setRequestBody(formBody);
        request.setAdditionalHeader("Content-Type", "application/x-www-form-urlencoded");
        return client(user).getPage(request);
    }

    protected static int status(Page page) {
        return page.getWebResponse().getStatusCode();
    }

    protected static String body(Page page) {
        return page.getWebResponse().getContentAsString();
    }

    protected static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    // ------------------------------------------------------------------ stored history

    /** Creates a job whose first saved revision holds {@code first} and a later one holds {@code second}. */
    protected FreeStyleProject createJobWithSecrets(String name, String first, String second) throws Exception {
        FreeStyleProject p = j.createFreeStyleProject(name);
        p.setDescription(OLD_DESCRIPTION);
        p.addProperty(new ParametersDefinitionProperty(new PasswordParameterDefinition("P", first, "")));
        p.save();
        Thread.sleep(1200);
        p.setDescription(NEW_DESCRIPTION);
        p.removeProperty(ParametersDefinitionProperty.class);
        p.addProperty(new ParametersDefinitionProperty(new PasswordParameterDefinition("P", second, "")));
        p.save();
        Thread.sleep(400);
        return p;
    }

    protected File historyDirectory(String name) {
        return new File(new File(new File(j.jenkins.getRootDir(), "config-history"), "jobs"), name);
    }

    protected List<File> revisions(String name) {
        File directory = historyDirectory(name);
        File[] children = directory.listFiles();
        List<File> revisions = new ArrayList<File>();
        if (children != null) {
            for (File child : children) {
                if (child.isDirectory() && new File(child, "config.xml").isFile()) {
                    revisions.add(child);
                }
            }
        }
        Collections.sort(revisions, new Comparator<File>() {
            public int compare(File a, File b) {
                return a.getName().compareTo(b.getName());
            }
        });
        return revisions;
    }

    protected String configXml(File revision) throws IOException {
        return Files.readString(new File(revision, "config.xml").toPath());
    }

    /** The encrypted value stored in a revision, or null when the revision has none. */
    protected static String encryptedValue(String xml) {
        int start = xml.indexOf("AQAAAB");
        if (start < 0) {
            return null;
        }
        int end = xml.indexOf('}', start);
        if (end < 0) {
            return null;
        }
        return xml.substring(start, end + 1);
    }

    /** Returns two saved revisions whose stored encrypted values differ. */
    protected File[] revisionsWithDifferentSecrets(String name) throws IOException {
        String firstValue = null;
        File firstRevision = null;
        for (File revision : revisions(name)) {
            String value = encryptedValue(configXml(revision));
            if (value == null) {
                continue;
            }
            if (firstValue == null) {
                firstValue = value;
                firstRevision = revision;
            } else if (!firstValue.equals(value)) {
                return new File[] {firstRevision, revision};
            }
        }
        fail("the job history did not contain two revisions with different stored values");
        return null;
    }

    /** Inserts a plain-text token into a stored revision, as a revision written by an older version would hold. */
    protected File addPlainTextToken(File revision, String token) throws IOException {
        File config = new File(revision, "config.xml");
        String xml = Files.readString(config.toPath());
        int end = xml.lastIndexOf("</project>");
        assertTrue("unexpected configuration layout", end > 0);
        xml = xml.substring(0, end) + "<authToken>" + token + "</authToken>" + xml.substring(end);
        Files.writeString(config.toPath(), xml);
        return revision;
    }

    /** Finds the archived directory a deleted job's history was moved to. */
    protected String deletedDirectory(String name) {
        File jobs = new File(new File(j.jenkins.getRootDir(), "config-history"), "jobs");
        File[] children = jobs.listFiles();
        if (children != null) {
            for (File child : children) {
                if (child.getName().startsWith(name + "_deleted_")) {
                    return child.getName();
                }
            }
        }
        fail("the deleted job's history directory was not found");
        return null;
    }
}
