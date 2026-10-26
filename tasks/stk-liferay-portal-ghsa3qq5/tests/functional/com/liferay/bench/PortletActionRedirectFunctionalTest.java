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
 * A portlet action that redirects to an ordinary destination still reaches the client.
 */
public class PortletActionRedirectFunctionalTest {

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
	public void testAllowListedLocationStillSent() throws Exception {
		RedirectTestSupport.Recorder recorder = PortletActionHarness.process(
			"http://google.com/landing");

		Assert.assertEquals(
			Collections.singletonList("http://google.com/landing"),
			recorder.redirects);
	}

	@Test
	public void testRelativeLocationStillSent() throws Exception {
		RedirectTestSupport.Recorder recorder = PortletActionHarness.process(
			"/web/guest");

		Assert.assertEquals(
			Collections.singletonList("/web/guest"), recorder.redirects);
	}

}
