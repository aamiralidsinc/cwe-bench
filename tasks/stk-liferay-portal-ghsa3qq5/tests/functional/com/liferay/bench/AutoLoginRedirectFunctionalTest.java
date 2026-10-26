package com.liferay.bench;

import com.liferay.portal.test.rule.LiferayUnitTestRule;

import java.util.Collections;

import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.ClassRule;
import org.junit.Rule;
import org.junit.Test;

/**
 * An auto-login provider that redirects to an ordinary destination still reaches the client.
 */
public class AutoLoginRedirectFunctionalTest {

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
	public void testAllowListedRedirectStillSent() throws Exception {
		RedirectTestSupport.Recorder recorder = AutoLoginHarness.run(
			"http://google.com/landing");

		Assert.assertEquals(
			Collections.singletonList("http://google.com/landing"),
			recorder.redirects);
	}

	@Test
	public void testRelativeRedirectStillSent() throws Exception {
		RedirectTestSupport.Recorder recorder = AutoLoginHarness.run(
			"/web/guest");

		Assert.assertEquals(
			Collections.singletonList("/web/guest"), recorder.redirects);
	}

}
