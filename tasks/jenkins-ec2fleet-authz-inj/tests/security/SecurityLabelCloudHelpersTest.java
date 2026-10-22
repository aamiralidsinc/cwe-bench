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
 * The label-based cloud's key-pair listing and connection test also use a stored
 * credential against the request's region/endpoint.
 */
@WithJenkins
class SecurityLabelCloudHelpersTest {
    private static final String KEYPAIRS = "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetLabelCloud/fillEc2KeyPairNameItems"
            + "?awsCredentialsId=&region=us-east-1&endpoint=";
    private static final String TEST_CONNECTION = "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetLabelCloud/testConnection"
            + "?awsCredentialsId=&region=us-east-1&endpoint=&fleet=";

    @Test
    void nonAdminPostToKeyPairListingIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "alice", HttpMethod.POST, KEYPAIRS,
                "a non-administrator POST was able to drive the label cloud's key-pair listing");
    }

    @Test
    void getRequestToKeyPairListingIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "admin", HttpMethod.GET, KEYPAIRS,
                "a safe-method GET was able to drive the label cloud's key-pair listing");
    }

    @Test
    void nonAdminPostToLabelTestConnectionIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "alice", HttpMethod.POST, TEST_CONNECTION,
                "a non-administrator POST was able to drive the label cloud's connection test");
    }

    @Test
    void getRequestToLabelTestConnectionIsRefused(JenkinsRule j) throws Exception {
        secure(j);
        assertRefused(j, "admin", HttpMethod.GET, TEST_CONNECTION,
                "a safe-method GET was able to drive the label cloud's connection test");
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
