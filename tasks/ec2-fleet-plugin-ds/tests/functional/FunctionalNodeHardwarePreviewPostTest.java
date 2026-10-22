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

/** An administrator submitting the node-hardware form (a POST) must still get the preview. */
@WithJenkins
class FunctionalNodeHardwarePreviewPostTest {

    @Test
    void adminCanPreviewInstanceTypesViaPost(JenkinsRule j) throws Exception {
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        final MockAuthorizationStrategy auth = new MockAuthorizationStrategy();
        auth.grant(Jenkins.ADMINISTER).everywhere().to("admin");
        j.jenkins.setAuthorizationStrategy(auth);
        j.jenkins.setCrumbIssuer(null);

        final JenkinsRule.WebClient wc = j.createWebClient();
        wc.login("admin");

        final WebRequest req = new WebRequest(new URL(j.getURL(),
                "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetCloud$NodeHardwareScaler/fillInstanceTypeItems"
                        + "?awsCredentialsId=&region=us-east-1&endpoint="),
                HttpMethod.POST);
        final Page page = wc.getPage(req);
        assertEquals(200, page.getWebResponse().getStatusCode());
    }
}
