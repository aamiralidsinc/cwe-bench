package com.amazon.jenkins.ec2fleet;

import java.net.URL;

import jenkins.model.Jenkins;
import org.htmlunit.FailingHttpStatusCodeException;
import org.htmlunit.HttpMethod;
import org.htmlunit.WebRequest;
import org.junit.jupiter.api.Test;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.MockAuthorizationStrategy;
import org.jvnet.hudson.test.junit.jupiter.WithJenkins;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.fail;

/**
 * The label-based cloud's region listing makes Jenkins talk to AWS with a stored
 * credential. Even an administrator must use a state-changing submission: a safe
 * method must not drive it. (The permission-only facet is covered elsewhere.)
 */
@WithJenkins
class SecurityLabelCloudRegionPostTest {
    private static final String REGIONS = "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetLabelCloud/fillRegionItems?awsCredentialsId=";

    @Test
    void adminGetToLabelCloudRegionListingIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "admin", HttpMethod.GET, REGIONS,
                "a safe-method GET was able to drive the label cloud's AWS-backed region listing");
    }

    /** Admin has ADMINISTER. CSRF crumbs are off so the method is judged on its own merits. */
    private static void secure(final JenkinsRule j) {
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        final MockAuthorizationStrategy auth = new MockAuthorizationStrategy();
        auth.grant(Jenkins.ADMINISTER).everywhere().to("admin");
        j.jenkins.setAuthorizationStrategy(auth);
        j.jenkins.setCrumbIssuer(null);
    }

    private static void assertRefused(final JenkinsRule j, final String user, final HttpMethod method,
                                      final String path, final String what) throws Exception {
        final JenkinsRule.WebClient wc = j.createWebClient();
        wc.login(user);
        final WebRequest req = new WebRequest(new URL(j.getURL(), path), method);
        try {
            wc.getPage(req);
            fail(what);
        } catch (final FailingHttpStatusCodeException e) {
            final int s = e.getStatusCode();
            assertTrue(s >= 400 && s < 500, "refusal must be a client error, got " + s);
        }
    }
}
