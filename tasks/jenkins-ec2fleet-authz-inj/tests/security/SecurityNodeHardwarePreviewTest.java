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
 * The node-hardware scaler's instance-type preview also makes Jenkins talk to AWS with a
 * stored credential. A non-administrator, or a safe-method request, must not drive it.
 */
@WithJenkins
class SecurityNodeHardwarePreviewTest {
    private static final String PREVIEW = "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetCloud$NodeHardwareScaler/fillInstanceTypeItems"
            + "?awsCredentialsId=&region=us-east-1&endpoint=";

    @Test
    void nonAdminGetToInstanceTypePreviewIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "alice", HttpMethod.GET, PREVIEW,
                "a non-administrator GET was able to drive the AWS-backed instance-type preview");
    }

    @Test
    void nonAdminPostToInstanceTypePreviewIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "alice", HttpMethod.POST, PREVIEW,
                "a non-administrator POST was able to drive the AWS-backed instance-type preview");
    }

    @Test
    void adminGetToInstanceTypePreviewIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "admin", HttpMethod.GET, PREVIEW,
                "a safe-method GET was able to drive the AWS-backed instance-type preview");
    }

    /** Admin has ADMINISTER, alice only overall READ. CSRF crumbs are off so a POST is judged on its own merits. */
    private static void secure(final JenkinsRule j) {
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        final MockAuthorizationStrategy auth = new MockAuthorizationStrategy();
        auth.grant(Jenkins.ADMINISTER).everywhere().to("admin");
        auth.grant(Jenkins.READ).everywhere().to("alice");
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
