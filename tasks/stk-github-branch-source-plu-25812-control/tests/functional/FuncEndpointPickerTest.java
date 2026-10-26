package org.jenkinsci.plugins.github_branch_source;

import static org.junit.Assert.assertTrue;

import org.junit.Test;

/** The endpoint picker keeps offering every legitimate choice to the people who configure it. */
public class FuncEndpointPickerTest extends ApiUriFixture {
    static final String NAVIGATOR = "org.jenkinsci.plugins.github_branch_source.GitHubSCMNavigator";
    static final String SOURCE = "org.jenkinsci.plugins.github_branch_source.GitHubSCMSource";
    static final String APP = "org.jenkinsci.plugins.github_branch_source.GitHubAppCredentials";
    static final String TRAIT = "org.jenkinsci.plugins.github_branch_source.SSHCheckoutTrait";
    static final String CONFIG = "org.jenkinsci.plugins.github_branch_source.GitHubConfiguration";

    @Test
    public void managerSeesOrganizationFolderAndSourceChoices() throws Exception {
        assertTrue("a server administrator lost the organization-folder choices",
                fetch("manager", rootPath(NAVIGATOR)).contains(API_URI));
        assertTrue("a server administrator lost the branch-source choices",
                fetch("manager", rootPath(SOURCE)).contains(API_URI));
    }

    @Test
    public void managerSeesCredentialAndTraitChoices() throws Exception {
        assertTrue("a server administrator lost the credential choices",
                fetch("manager", rootPath(APP)).contains(API_URI));
        assertTrue("a server administrator lost the checkout trait choices",
                fetch("manager", rootPath(TRAIT)).contains(API_URI));
    }

    @Test
    public void managerSeesGlobalConfigurationChoices() throws Exception {
        assertTrue("a server administrator lost the global choices",
                fetch("manager", rootPath(CONFIG)).contains(API_URI));
    }

    @Test
    public void itemConfiguratorSeesOrganizationFolderAndSourceChoices() throws Exception {
        assertTrue("a user configuring an item lost the organization-folder choices",
                fetch("configurator", itemPath(NAVIGATOR)).contains(API_URI));
        assertTrue("a user configuring an item lost the branch-source choices",
                fetch("configurator", itemPath(SOURCE)).contains(API_URI));
    }

    @Test
    public void itemConfiguratorSeesCredentialAndTraitChoices() throws Exception {
        assertTrue("a user configuring an item lost the credential choices",
                fetch("configurator", itemPath(APP)).contains(API_URI));
        assertTrue("a user configuring an item lost the checkout trait choices",
                fetch("configurator", itemPath(TRAIT)).contains(API_URI));
    }

    @Test
    public void publicGitHubChoiceStaysOnEverySurface() throws Exception {
        for (String fqcn : new String[] {NAVIGATOR, SOURCE, APP, TRAIT, CONFIG}) {
            assertTrue("the ordinary public GitHub choice disappeared from " + fqcn,
                    fetch("manager", rootPath(fqcn)).contains("GitHub"));
        }
    }
}
