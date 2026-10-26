package org.jenkinsci.plugins.github_branch_source;

import static org.junit.Assert.assertFalse;

import org.junit.Test;

/** The global endpoint picker must not enumerate registered servers for a user who does not administer the server. */
public class SecGlobalConfigurationApiUriTest extends ApiUriFixture {
    static final String CLASS = "org.jenkinsci.plugins.github_branch_source.GitHubConfiguration";

    @Test
    public void rootScopeDeniedToReadOnlyUser() throws Exception {
        String text = fetch("reader", rootPath(CLASS));
        assertFalse("the registered server list leaked outside any item", text.contains(API_URI));
    }
}
