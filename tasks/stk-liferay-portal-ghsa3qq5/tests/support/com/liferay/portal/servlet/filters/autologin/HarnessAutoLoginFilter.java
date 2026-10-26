package com.liferay.portal.servlet.filters.autologin;

import javax.servlet.FilterChain;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * Exposes the filter's normal request processing so a test can drive the same path the servlet
 * container drives.
 */
public class HarnessAutoLoginFilter extends AutoLoginFilter {

	public void process(
			HttpServletRequest httpServletRequest,
			HttpServletResponse httpServletResponse, FilterChain filterChain)
		throws Exception {

		processFilter(httpServletRequest, httpServletResponse, filterChain);
	}

}
