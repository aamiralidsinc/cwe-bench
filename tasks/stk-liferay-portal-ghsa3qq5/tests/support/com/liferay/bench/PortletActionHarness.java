package com.liferay.bench;

import com.liferay.portal.kernel.model.Portlet;
import com.liferay.portal.kernel.model.PortletApp;
import com.liferay.portal.kernel.portlet.ActionResult;
import com.liferay.portal.kernel.portlet.PortletContainer;
import com.liferay.portal.kernel.portlet.PortletContainerException;
import com.liferay.portal.kernel.portlet.PortletContainerUtil;

import java.lang.reflect.InvocationHandler;

import java.util.Collections;
import java.util.List;

/**
 * Drives the portal's own portlet-action redirect path with a container that returns a supplied
 * destination, exactly as a portlet action's sendRedirect does at run time.
 */
public final class PortletActionHarness {

	public static RedirectTestSupport.Recorder process(String location)
		throws PortletContainerException {
		PortletApp portletApp = RedirectTestSupport.proxy(
			PortletApp.class,
			(proxy, method, args) -> {
				if (method.getName().equals("getSpecMajorVersion")) {
					return Integer.valueOf(2);
				}

				return RedirectTestSupport.defaultValue(method.getReturnType());
			});

		Portlet portlet = RedirectTestSupport.proxy(
			Portlet.class,
			(proxy, method, args) -> {
				if (method.getName().equals("isActionURLRedirect")) {
					return Boolean.FALSE;
				}

				if (method.getName().equals("getPortletApp")) {
					return portletApp;
				}

				return RedirectTestSupport.defaultValue(method.getReturnType());
			});

		PortletContainer portletContainer = RedirectTestSupport.proxy(
			PortletContainer.class,
			(proxy, method, args) -> {
				if (method.getName().equals("processAction")) {
					return new ActionResult(
						Collections.emptyList(), location);
				}

				return RedirectTestSupport.defaultValue(method.getReturnType());
			});

		new PortletContainerUtil().setPortletContainer(portletContainer);

		RedirectTestSupport.Recorder recorder =
			RedirectTestSupport.newRecorder();

		PortletContainerUtil.processAction(
			recorder.request(), recorder.response(), portlet);

		return recorder;
	}

	private PortletActionHarness() {
	}

}
