package org.jenkinsci.plugins.github_branch_source;

import static org.junit.Assert.assertFalse;

import org.junit.Test;

/** The organization-folder endpoint picker must not enumerate registered servers for a user who may configure nothing. */
public class SecNavigatorApiUriTest extends ApiUriFixture {
    static final String CLASS = "org.jenkinsci.plugins.github_branch_source.GitHubSCMNavigator";

    @Test
    public void rootScopeDeniedToReadOnlyUser() throws Exception {
        assertNoLeak(fetch("reader", rootPath(CLASS)));
    }

    @Test
    public void itemScopeDeniedToReadOnlyUser() throws Exception {
        assertNoLeak(fetch("reader", itemPath(CLASS)));
    }

    @Test
    public void itemScopeDeniedToBuilder() throws Exception {
        assertNoLeak(fetch("builder", itemPath(CLASS)));
    }

    @Test
    public void rootScopeDeniedToItemReader() throws Exception {
        assertNoLeak(fetch("itemReader", rootPath(CLASS)));
    }

    private static void assertNoLeak(String text) {
        assertFalse("the registered server list leaked to a caller who may not configure the request", text.contains(API_URI));
    }
}
