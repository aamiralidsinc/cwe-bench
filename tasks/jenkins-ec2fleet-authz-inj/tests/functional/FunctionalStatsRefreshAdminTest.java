package com.amazon.jenkins.ec2fleet;

import java.net.URL;

import jenkins.model.Jenkins;
import org.htmlunit.HttpMethod;
import org.htmlunit.Page;
import org.htmlunit.WebRequest;
import org.junit.jupiter.api.Test;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.MockAuthorizationStrategy;
import org.jvnet.hudson.test.junit.jupiter.WithJenkins;

import static org.junit.jupiter.api.Assertions.assertEquals;

/** An administrator must still be able to trigger a cloud refresh with a POST. */
@WithJenkins
class FunctionalStatsRefreshAdminTest {

    @Test
    void adminCanTriggerRefresh(JenkinsRule j) throws Exception {
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        final MockAuthorizationStrategy auth = new MockAuthorizationStrategy();
        auth.grant(Jenkins.ADMINISTER).everywhere().to("admin");
        j.jenkins.setAuthorizationStrategy(auth);
        j.jenkins.setCrumbIssuer(null);

        final JenkinsRule.WebClient wc = j.createWebClient();
        wc.login("admin");

        final WebRequest req = new WebRequest(new URL(j.getURL(), "ec2-fleet/refresh"), HttpMethod.POST);
        final Page page = wc.getPage(req);
        assertEquals(200, page.getWebResponse().getStatusCode());
    }
}
