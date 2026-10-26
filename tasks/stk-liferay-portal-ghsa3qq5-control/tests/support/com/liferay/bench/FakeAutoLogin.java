package com.liferay.bench;

import com.liferay.portal.kernel.security.auto.login.AutoLogin;
import com.liferay.portal.kernel.security.auto.login.AutoLoginException;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * Stands in for an auto-login provider: it hands the portal the destination it wants the user
 * sent to after authentication, which is the same contract the shipped providers implement.
 */
public class FakeAutoLogin implements AutoLogin {

	public static void setRedirect(String redirect) {
		_redirect = redirect;
	}

	@Override
	public String[] login(
			HttpServletRequest httpServletRequest,
			HttpServletResponse httpServletResponse)
		throws AutoLoginException {

		if (_redirect != null) {
			httpServletRequest.setAttribute(
				AUTO_LOGIN_REDIRECT, _redirect);
		}

		return null;
	}

	private static String _redirect;

}
