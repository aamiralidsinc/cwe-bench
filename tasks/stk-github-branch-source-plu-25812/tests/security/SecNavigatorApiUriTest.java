package org.jenkinsci.plugins.github_branch_source;

import static org.junit.Assert.assertFalse;

import org.junit.Test;

/** The organization-folder endpoint picker must not enumerate registered servers for a user who may configure nothing. */
public class SecNavigatorApiUriTest extends ApiUriFixture {
    static final String CLASS = "org.jenkinsci.plugins.github_branch_source.GitHubSCMNavigator";

    @Test
    public void rootScopeDeniedToReadOnlyUser() throws Exception {
        String text = fetch("reader", rootPath(CLASS));
        assertFalse("the registered server list leaked outside any item", text.contains(API_URI));
    }

    @Test
    public void itemScopeDeniedToReadOnlyUser() throws Exception {
        String text = fetch("reader", itemPath(CLASS));
        assertFalse("the registered server list leaked for an item the user may not configure", text.contains(API_URI));
    }
}
