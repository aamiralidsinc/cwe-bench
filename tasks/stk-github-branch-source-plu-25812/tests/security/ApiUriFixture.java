package org.jenkinsci.plugins.github_branch_source;

import static org.junit.Assert.assertTrue;

import hudson.model.Item;
import java.net.URL;
import jenkins.model.Jenkins;
import org.htmlunit.FailingHttpStatusCodeException;
import org.htmlunit.Page;
import org.junit.After;
import org.junit.Before;
import org.junit.Rule;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.MockAuthorizationStrategy;
import org.jvnet.hudson.test.MockFolder;

/**
 * Shared setup: a registered GitHub Enterprise server, a folder, and three users with the
 * permissions the endpoint picker answers to. Every probe goes through the descriptor form
 * fill over HTTP, the same way the configuration page loads its choices.
 */
abstract class ApiUriFixture {

    static final String API_URI = "https://ghe-stk25812.example/api/v3";
    static final String API_NAME = "GHE-STK25812";

    @Rule
    public JenkinsRule j = new JenkinsRule();

    MockFolder folder;
    private Endpoint endpoint;

    @Before
    public void setUpFixture() throws Exception {
        endpoint = new Endpoint(API_URI, API_NAME);
        GitHubConfiguration.get().addEndpoint(endpoint);
        folder = j.createFolder("team");
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        MockAuthorizationStrategy auth = new MockAuthorizationStrategy();
        auth.grant(Jenkins.READ).everywhere().to("reader");
        auth.grant(Item.READ).onItems(folder).to("reader");
        auth.grant(Jenkins.ADMINISTER).everywhere().to("manager");
        auth.grant(Jenkins.READ).everywhere().to("configurator");
        auth.grant(Item.READ, Item.CONFIGURE, Item.EXTENDED_READ)
                .onItems(folder)
                .to("configurator");
        j.jenkins.setAuthorizationStrategy(auth);
        j.jenkins.setCrumbIssuer(null);
    }

    @After
    public void tearDownFixture() {
        GitHubConfiguration.get().removeEndpoint(endpoint);
    }

    static String rootPath(String fqcn) {
        return "descriptorByName/" + fqcn + "/fillApiUriItems";
    }

    String itemPath(String fqcn) {
        return "job/" + folder.getName() + "/descriptorByName/" + fqcn + "/fillApiUriItems";
    }

    String fetch(String user, String path) throws Exception {
        JenkinsRule.WebClient wc = j.createWebClient();
        wc.login(user);
        try {
            Page page = wc.getPage(new URL(j.getURL(), path));
            return page.getWebResponse().getContentAsString();
        } catch (FailingHttpStatusCodeException e) {
            int status = e.getStatusCode();
            assertTrue("a refusal must be a client error, got " + status, status >= 400 && status < 500);
            return "";
        }
    }
}
