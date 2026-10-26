package com.liferay.bench;

import com.liferay.portal.kernel.security.auto.login.AutoLogin;
import com.liferay.portal.kernel.test.ReflectionTestUtil;
import com.liferay.portal.servlet.filters.autologin.HarnessAutoLoginFilter;
import com.liferay.registry.collections.ServiceTrackerList;

import java.lang.reflect.Proxy;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Drives the portal's auto-login filter with one provider registered, the way the filter runs
 * when a provider returns after deciding where the user should go.
 */
public final class AutoLoginHarness {

	public static synchronized void ensure() throws Exception {
		if (_ready) {
			return;
		}

		RedirectTestSupport.initKernel();

		Class<?> filterClass = Class.forName(
			"com.liferay.portal.servlet.filters.autologin.AutoLoginFilter");

		final List<AutoLogin> autoLogins = new ArrayList<>();

		autoLogins.add(_fakeAutoLogin);

		ServiceTrackerList<AutoLogin> serviceTrackerList =
			(ServiceTrackerList<AutoLogin>)Proxy.newProxyInstance(
				ServiceTrackerList.class.getClassLoader(),
				new Class<?>[] {ServiceTrackerList.class},
				(proxy, method, args) -> {
					String name = method.getName();

					if (name.equals("close")) {
						return null;
					}

					if (name.equals("add") && (args != null) &&
						(args.length == 2) && (args[0] instanceof AutoLogin)) {

						autoLogins.add((AutoLogin)args[0]);

						return Boolean.TRUE;
					}

					return method.invoke(autoLogins, args);
				});

		ReflectionTestUtil.setFieldValue(
			filterClass, "_autoLogins", serviceTrackerList);

		_ready = true;
	}

	public static RedirectTestSupport.Recorder run(String redirect)
		throws Exception {

		ensure();

		FakeAutoLogin.setRedirect(redirect);

		RedirectTestSupport.Recorder recorder =
			RedirectTestSupport.newRecorder();

		new HarnessAutoLoginFilter().process(
			recorder.request(), recorder.response(),
			RedirectTestSupport.noOpFilterChain());

		return recorder;
	}

	private static final FakeAutoLogin _fakeAutoLogin = new FakeAutoLogin();
	private static boolean _ready;

	private AutoLoginHarness() {
	}

}
