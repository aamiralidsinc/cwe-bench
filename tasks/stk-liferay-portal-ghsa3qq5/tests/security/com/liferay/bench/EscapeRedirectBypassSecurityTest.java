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
 * A destination whose authority is empty must not be taken for a relative path.
 */
public class EscapeRedirectBypassSecurityTest {

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
	public void testEmptyAuthorityRelative() {
		Assert.assertNull(_portalImpl.escapeRedirect("///evil.example"));
		Assert.assertNull(_portalImpl.escapeRedirect("////evil.example"));
	}

	@Test
	public void testEmptyAuthorityRelativeInIPMode() {
		RedirectTestSupport.useIPAllowList("127.0.0.1", "SERVER_IP");

		Assert.assertNull(_portalImpl.escapeRedirect("///evil.example"));
	}

	@Test
	public void testEmptyAuthorityRelativeWithPath() {
		Assert.assertNull(
			_portalImpl.escapeRedirect("///evil.example/landing"));
		Assert.assertNull(
			_portalImpl.escapeRedirect("////evil.example/landing"));
	}

	private final PortalImpl _portalImpl = new PortalImpl();

}
