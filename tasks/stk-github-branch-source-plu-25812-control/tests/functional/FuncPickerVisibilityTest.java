package org.jenkinsci.plugins.github_branch_source;

import static org.junit.Assert.assertTrue;

import hudson.model.User;
import hudson.security.ACL;
import hudson.security.ACLContext;
import org.junit.Test;

/** The endpoint picker stays visible wherever it is offered to the people who configure it. */
public class FuncPickerVisibilityTest extends ApiUriFixture {

    @Test
    public void itemConfiguratorSeesThePicker() throws Exception {
        try (ACLContext ctx = ACL.as2(User.getById("configurator", true).impersonate2())) {
            assertTrue("the organization-folder picker vanished for an item configurator",
                    j.jenkins.getDescriptorByType(GitHubSCMNavigator.DescriptorImpl.class).isApiUriSelectable());
            assertTrue("the branch-source picker vanished for an item configurator",
                    j.jenkins.getDescriptorByType(GitHubSCMSource.DescriptorImpl.class).isApiUriSelectable());
            assertTrue("the credential picker vanished for an item configurator",
                    j.jenkins.getDescriptorByType(GitHubAppCredentials.DescriptorImpl.class).isApiUriSelectable());
        }
    }

    @Test
    public void managerSeesThePicker() throws Exception {
        try (ACLContext ctx = ACL.as2(User.getById("manager", true).impersonate2())) {
            assertTrue("the organization-folder picker vanished for a server administrator",
                    j.jenkins.getDescriptorByType(GitHubSCMNavigator.DescriptorImpl.class).isApiUriSelectable());
            assertTrue("the branch-source picker vanished for a server administrator",
                    j.jenkins.getDescriptorByType(GitHubSCMSource.DescriptorImpl.class).isApiUriSelectable());
            assertTrue("the credential picker vanished for a server administrator",
                    j.jenkins.getDescriptorByType(GitHubAppCredentials.DescriptorImpl.class).isApiUriSelectable());
        }
    }
}
