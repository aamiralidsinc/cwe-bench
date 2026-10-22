package com.amazon.jenkins.ec2fleet;

import java.net.URL;
import java.util.Collections;

import hudson.model.Computer;
import hudson.model.Node;
import hudson.slaves.JNLPLauncher;
import jenkins.model.Jenkins;
import org.htmlunit.HttpMethod;
import org.htmlunit.Page;
import org.htmlunit.WebRequest;
import org.junit.jupiter.api.Test;
import org.jvnet.hudson.test.JenkinsRule;
import org.jvnet.hudson.test.MockAuthorizationStrategy;
import org.jvnet.hudson.test.junit.jupiter.WithJenkins;

import static org.junit.jupiter.api.Assertions.assertNull;

/**
 * Retiring an agent is an ordinary operator action, not an administrator-only one: a user
 * who holds the right to delete that agent (and nothing more) must still be able to do it.
 */
@WithJenkins
class FunctionalAgentRetirementTest {

    @Test
    void operatorWithDeletePermissionCanRetireAgent(JenkinsRule j) throws Exception {
        j.jenkins.setSecurityRealm(j.createDummySecurityRealm());
        final MockAuthorizationStrategy auth = new MockAuthorizationStrategy();
        auth.grant(Jenkins.READ).everywhere().to("operator");
        auth.grant(Computer.DELETE).everywhere().to("operator");
        j.jenkins.setAuthorizationStrategy(auth);
        j.jenkins.setCrumbIssuer(null);

        final EC2FleetNode node = new EC2FleetNode("i-0123456789abcdef0", "fleet agent", "/tmp",
                1, Node.Mode.NORMAL, "fleet", Collections.emptyList(), "test-cloud", new JNLPLauncher(), 1);
        j.jenkins.addNode(node);

        final JenkinsRule.WebClient wc = j.createWebClient();
        wc.login("operator");
        final String path = "computer/" + node.getNodeName() + "/doDelete";
        final Page page = wc.getPage(new WebRequest(new URL(j.getURL(), path), HttpMethod.POST));
        assertNull(j.jenkins.getNode(node.getNodeName()),
                "the operator's retirement submission must still remove the agent (status "
                        + page.getWebResponse().getStatusCode() + ")");
    }
}
