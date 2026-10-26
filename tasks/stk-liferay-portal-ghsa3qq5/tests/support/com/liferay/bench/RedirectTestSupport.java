package com.liferay.bench;

import com.liferay.portal.kernel.redirect.RedirectURLSettings;
import com.liferay.portal.kernel.redirect.RedirectURLSettingsUtil;
import com.liferay.portal.kernel.test.ReflectionTestUtil;
import com.liferay.portal.kernel.util.PortalUtil;
import com.liferay.portal.util.PortalImpl;
import com.liferay.registry.BasicRegistryImpl;
import com.liferay.registry.RegistryUtil;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;

import java.net.URI;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import javax.servlet.FilterChain;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

/**
 * Shared, submission-independent bookkeeping for the redirect suites: mocks for the servlet
 * interfaces, the redirect settings stub the product's check reads, and a helper that decides
 * whether a redirect target leaves the site.
 */
public final class RedirectTestSupport {

	public static final Set<String> ALLOWED_HOSTS = new HashSet<>(
		Arrays.asList("google.com", "localhost"));

	public static void initKernel() {
		synchronized (RedirectTestSupport.class) {
			if (_initialized) {
				return;
			}

			RegistryUtil.setRegistry(new BasicRegistryImpl());

			new PortalUtil().setPortal(new PortalImpl());

			_initialized = true;
		}
	}

	public static void useDomainAllowList(String... domains) {
		useSettings("domain", domains, new String[] {"127.0.0.1", "SERVER_IP"});
	}

	public static void useIPAllowList(String... ips) {
		useSettings("ip", new String[] {"google.com", "localhost"}, ips);
	}

	public static void useSettings(
		String mode, String[] domains, String[] ips) {

		RedirectURLSettingsImpl settings = new RedirectURLSettingsImpl();

		settings.allowedDomains = domains;
		settings.allowedIPs = ips;
		settings.securityMode = mode;

		_originalSettings = ReflectionTestUtil.getAndSetFieldValue(
			RedirectURLSettingsUtil.class, "_redirectURLSettings", settings);

		_settingsInstalled = true;
	}

	public static void restoreSettings() {
		if (_settingsInstalled) {
			ReflectionTestUtil.setFieldValue(
				RedirectURLSettingsUtil.class, "_redirectURLSettings",
				_originalSettings);

			_settingsInstalled = false;
		}
	}

	/**
	 * True when a recorded redirect target would leave the site: an authority-relative
	 * reference, or an absolute reference whose host is not one of the allowed hosts.
	 */
	public static boolean isUnsafe(String target) {
		if (target == null) {
			return false;
		}

		String trimmed = target.trim();

		if (trimmed.startsWith("//")) {
			return true;
		}

		try {
			URI uri = new URI(trimmed);

			String host = uri.getHost();

			if (host == null) {
				return false;
			}

			return !ALLOWED_HOSTS.contains(host.toLowerCase(Locale.ROOT));
		}
		catch (Exception exception) {
			return false;
		}
	}

	public static boolean anyUnsafe(List<String> targets) {
		for (String target : targets) {
			if (isUnsafe(target)) {
				return true;
			}
		}

		return false;
	}

	public static final class Recorder {

		public final List<String> redirects = new ArrayList<>();
		public final List<Integer> clientErrors = new ArrayList<>();

		public HttpServletRequest request() {
			return RedirectTestSupport.request(this);
		}

		public HttpServletResponse response() {
			return RedirectTestSupport.response(this);
		}
	}

	public static Recorder newRecorder() {
		return new Recorder();
	}

	public static FilterChain noOpFilterChain() {
		return (FilterChain)Proxy.newProxyInstance(
			FilterChain.class.getClassLoader(), new Class<?>[] {FilterChain.class},
			(proxy, method, args) -> null);
	}

	public static HttpServletRequest request(Recorder recorder) {
		return (HttpServletRequest)Proxy.newProxyInstance(
			HttpServletRequest.class.getClassLoader(),
			new Class<?>[] {HttpServletRequest.class},
			new RequestHandler(recorder));
	}

	public static HttpServletResponse response(Recorder recorder) {
		return (HttpServletResponse)Proxy.newProxyInstance(
			HttpServletResponse.class.getClassLoader(),
			new Class<?>[] {HttpServletResponse.class},
			new ResponseHandler(recorder));
	}

	public static <T> T proxy(Class<T> clazz, InvocationHandler handler) {
		return clazz.cast(
			Proxy.newProxyInstance(
				clazz.getClassLoader(), new Class<?>[] {clazz}, handler));
	}

	public static Object defaultValue(Class<?> type) {
		if (!type.isPrimitive()) {
			return null;
		}

		if (type == boolean.class) {
			return Boolean.FALSE;
		}

		if (type == int.class) {
			return Integer.valueOf(0);
		}

		if (type == long.class) {
			return Long.valueOf(0);
		}

		if (type == short.class) {
			return Short.valueOf((short)0);
		}

		if (type == byte.class) {
			return Byte.valueOf((byte)0);
		}

		if (type == char.class) {
			return Character.valueOf((char)0);
		}

		if (type == float.class) {
			return Float.valueOf(0);
		}

		if (type == double.class) {
			return Double.valueOf(0);
		}

		return null;
	}

	private static final class RequestHandler implements InvocationHandler {

		private RequestHandler(Recorder recorder) {
			_recorder = recorder;
		}

		@Override
		public Object invoke(Object proxy, java.lang.reflect.Method method, Object[] args)
			throws Throwable {

			String name = method.getName();

			if (name.equals("getAttribute")) {
				return _attributes.get((String)args[0]);
			}

			if (name.equals("setAttribute")) {
				_attributes.put((String)args[0], args[1]);

				return null;
			}

			if (name.equals("removeAttribute")) {
				_attributes.remove((String)args[0]);

				return null;
			}

			if (name.equals("getSession")) {
				return _session;
			}

			if (name.equals("getRemoteUser")) {
				return null;
			}

			if (name.equals("getRequestURI")) {
				return "/";
			}

			if (name.equals("getServerName")) {
				return "localhost";
			}

			if (name.equals("getServerPort")) {
				return Integer.valueOf(8080);
			}

			if (name.equals("getScheme")) {
				return "http";
			}

			if (name.equals("getContextPath")) {
				return "";
			}

			if (name.equals("getMethod")) {
				return "GET";
			}

			if (name.equals("getProtocol")) {
				return "HTTP/1.1";
			}

			if (name.equals("isSecure")) {
				return Boolean.FALSE;
			}

			if (name.equals("getParameterMap")) {
				return new HashMap<String, String[]>();
			}

			return defaultValue(method.getReturnType());
		}

		private final Map<String, Object> _attributes = new HashMap<>();
		private final Recorder _recorder;

		private final HttpSession _session = (HttpSession)Proxy.newProxyInstance(
			HttpSession.class.getClassLoader(), new Class<?>[] {HttpSession.class},
			(proxy, method, args) -> {
				if (method.getName().equals("getId")) {
					return "bench-session";
				}

				return defaultValue(method.getReturnType());
			});
	}

	private static final class ResponseHandler implements InvocationHandler {

		private ResponseHandler(Recorder recorder) {
			_recorder = recorder;
		}

		@Override
		public Object invoke(Object proxy, java.lang.reflect.Method method, Object[] args)
			throws Throwable {

			String name = method.getName();

			if (name.equals("sendRedirect")) {
				_recorder.redirects.add((String)args[0]);

				return null;
			}

			if (name.equals("sendError")) {
				_recorder.clientErrors.add((Integer)args[0]);

				return null;
			}

			if (name.equals("isCommitted")) {
				return Boolean.FALSE;
			}

			return defaultValue(method.getReturnType());
		}

		private final Recorder _recorder;
	}

	private static class RedirectURLSettingsImpl implements RedirectURLSettings {

		@Override
		public String[] getAllowedDomains(long companyId) {
			return allowedDomains;
		}

		@Override
		public String[] getAllowedIPs(long companyId) {
			return allowedIPs;
		}

		@Override
		public String getSecurityMode(long companyId) {
			return securityMode;
		}

		protected String[] allowedDomains = new String[0];
		protected String[] allowedIPs = new String[] {"127.0.0.1", "SERVER_IP"};
		protected String securityMode = "domain";

	}

	private static boolean _initialized;
	private static boolean _settingsInstalled;
	private static RedirectURLSettings _originalSettings;

}
