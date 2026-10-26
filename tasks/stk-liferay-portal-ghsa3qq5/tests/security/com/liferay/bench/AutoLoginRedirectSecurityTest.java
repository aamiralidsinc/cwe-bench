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
 * The destination an auto-login provider hands the portal must be checked before it is sent.
 */
public class AutoLoginRedirectSecurityTest {

	@ClassRule
	@Rule
	public static final LiferayUnitTestRule liferayUnitTestRule =
		LiferayUnitTestRule.INSTANCE;

	@BeforeClass
	public static void setUpClass() throws Exception {
		RedirectTestSupport.initKernel();

		AutoLoginHarness.ensure();
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
	public void testExternalAbsoluteRedirectIsNotSent() throws Exception {
		RedirectTestSupport.Recorder recorder = AutoLoginHarness.run(
			"http://evil.example/landing");

		Assert.assertFalse(
			"the portal sent an unsanctioned destination: " +
				recorder.redirects,
			RedirectTestSupport.anyUnsafe(recorder.redirects));
	}

	@Test
	public void testProtocolRelativeRedirectIsNotSent() throws Exception {
		RedirectTestSupport.Recorder recorder = AutoLoginHarness.run(
			"///evil.example");

		Assert.assertFalse(
			"the portal sent an unsanctioned destination: " +
				recorder.redirects,
			RedirectTestSupport.anyUnsafe(recorder.redirects));
	}

}
