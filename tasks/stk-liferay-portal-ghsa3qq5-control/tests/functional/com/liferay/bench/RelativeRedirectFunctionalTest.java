package com.liferay.bench;

import com.liferay.portal.test.rule.LiferayUnitTestRule;
import com.liferay.portal.util.PortalImpl;

import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.ClassRule;
import org.junit.Rule;
import org.junit.Test;

/**
 * Ordinary relative destinations and configured destinations keep working.
 */
public class RelativeRedirectFunctionalTest {

	@ClassRule
	@Rule
	public static final LiferayUnitTestRule liferayUnitTestRule =
		LiferayUnitTestRule.INSTANCE;

	@BeforeClass
	public static void setUpClass() {
		RedirectTestSupport.initKernel();
	}

	@Before
	public void setUp() {
		RedirectTestSupport.useDomainAllowList("google.com", "localhost");
	}

	@After
	public void tearDown() {
		RedirectTestSupport.restoreSettings();
	}

	@Test
	public void testAllowListedTargetsUnchanged() {
		Assert.assertEquals(
			"http://google.com",
			_portalImpl.escapeRedirect("http://google.com"));
		Assert.assertEquals(
			"https://google.com:8080/a/b;c=d?e=f&g=h#x=y",
			_portalImpl.escapeRedirect(
				"https://google.com:8080/a/b;c=d?e=f&g=h#x=y"));
		Assert.assertEquals(
			"http://localhost", _portalImpl.escapeRedirect("http://localhost"));
		Assert.assertNull(_portalImpl.escapeRedirect("http://liferay.com"));
	}

	@Test
	public void testRelativeTargetsUnchanged() {
		Assert.assertEquals("/", _portalImpl.escapeRedirect("/"));
		Assert.assertEquals(
			"/web/guest", _portalImpl.escapeRedirect("/web/guest"));
		Assert.assertEquals(
			"/a/b;c=d?e=f&g=h#x=y",
			_portalImpl.escapeRedirect("/a/b;c=d?e=f&g=h#x=y"));
		Assert.assertEquals(
			"/web/http:", _portalImpl.escapeRedirect("/web/http:"));
		Assert.assertEquals(
			"web/http:", _portalImpl.escapeRedirect("web/http:"));
		Assert.assertEquals(
			"test@google.com",
			_portalImpl.escapeRedirect("test@google.com"));
	}

	private final PortalImpl _portalImpl = new PortalImpl();

}
