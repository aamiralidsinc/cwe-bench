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
import static org.junit.jupiter.api.Assertions.assertTrue;

/** An administrator submitting the cloud form (a POST) must still be able to list AWS regions. */
@WithJenkins
class FunctionalAdminRegionListingTest {

    @Test
    void adminCanListRegions(JenkinsRule j) throws Exception {
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        final MockAuthorizationStrategy auth = new MockAuthorizationStrategy();
        auth.grant(Jenkins.ADMINISTER).everywhere().to("admin");
        j.jenkins.setAuthorizationStrategy(auth);
        j.jenkins.setCrumbIssuer(null);

        final JenkinsRule.WebClient wc = j.createWebClient();
        wc.login("admin");

        final WebRequest req = new WebRequest(new URL(j.getURL(),
                "descriptorByName/com.amazon.jenkins.ec2fleet.EC2FleetCloud/fillRegionItems?awsCredentialsId="),
                HttpMethod.POST);
        final Page page = wc.getPage(req);
        assertEquals(200, page.getWebResponse().getStatusCode());
        final String body = page.getWebResponse().getContentAsString();
        assertTrue(body.contains("us-east-1"), "region listing should include standard AWS regions");
    }
}
