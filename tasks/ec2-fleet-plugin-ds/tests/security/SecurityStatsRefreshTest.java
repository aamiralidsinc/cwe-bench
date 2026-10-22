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
 * The plugin's root action exposes an operation that forces the configured clouds to
 * refresh their state from AWS with their stored credentials. Only an administrator,
 * through a state-changing request, may trigger it.
 */
@WithJenkins
class SecurityStatsRefreshTest {
    private static final String REFRESH = "ec2-fleet/refresh";

    @Test
    void nonAdminCannotTriggerRefresh(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "alice", HttpMethod.GET, REFRESH,
                "a non-administrator was able to trigger the AWS-backed cloud refresh");
    }

    @Test
    void nonAdminPostToRefreshIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "alice", HttpMethod.POST, REFRESH,
                "a non-administrator POST was able to trigger the AWS-backed cloud refresh");
    }

    @Test
    void adminGetToRefreshIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "admin", HttpMethod.GET, REFRESH,
                "a safe-method GET was able to trigger the AWS-backed cloud refresh");
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
