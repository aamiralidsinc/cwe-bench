package com.liferay.bench;

import com.liferay.portal.test.rule.LiferayUnitTestRule;

import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.ClassRule;
import org.junit.Rule;
import org.junit.Test;

/**
 * The destination a portlet action hands the portal must be checked before it is sent.
 */
public class PortletActionRedirectSecurityTest {

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
	public void testExternalAbsoluteLocationIsNotSent()
		throws Exception {
		RedirectTestSupport.Recorder recorder = PortletActionHarness.process(
			"http://evil.example/landing");

		Assert.assertFalse(
			"the portal sent an unsanctioned destination: " +
				recorder.redirects,
			RedirectTestSupport.anyUnsafe(recorder.redirects));
	}

	@Test
	public void testProtocolRelativeLocationIsNotSent()
		throws Exception {
		RedirectTestSupport.Recorder recorder = PortletActionHarness.process(
			"///evil.example");

		Assert.assertFalse(
			"the portal sent an unsanctioned destination: " +
				recorder.redirects,
			RedirectTestSupport.anyUnsafe(recorder.redirects));
	}

}
