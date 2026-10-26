package org.fao.geonet.kernel.security.shibboleth;

import bench.HandlerHarness;
import bench.RedirectProbe;
import org.fao.geonet.ApplicationContextHolder;
import org.junit.After;
import org.junit.Test;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;

import javax.servlet.FilterChain;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * The Shibboleth pre-authentication handshake keeps honouring an in-application
 * destination and keeps passing the request down the chain when none is supplied.
 */
public class FunctionalShibbolethRedirectTest {

    @After
    public void tearDown() {
        ApplicationContextHolder.clear();
        SecurityContextHolder.clearContext();
    }

    private void authenticate(String destination, HttpServletResponse response,
                              FilterChain chain) throws Exception {
        ShibbolethUserConfiguration configuration = mock(ShibbolethUserConfiguration.class);
        when(configuration.getUsernameKey()).thenReturn("uid");

        ShibbolethUserUtils userUtils = mock(ShibbolethUserUtils.class);
        UserDetails user = new User("alice", "", AuthorityUtils.NO_AUTHORITIES);
        when(userUtils.setupUser(any(), any())).thenReturn(user);

        ConfigurableApplicationContext applicationContext =
            mock(ConfigurableApplicationContext.class);
        when(applicationContext.getBean(ShibbolethUserConfiguration.class))
            .thenReturn(configuration);
        when(applicationContext.getBean(ShibbolethUserUtils.class)).thenReturn(userUtils);
        ApplicationContextHolder.set(applicationContext);

        ShibbolethPreAuthFilter filter = new ShibbolethPreAuthFilter();
        filter.setRequestCache(null);

        HttpServletRequest request = mock(HttpServletRequest.class);
        HttpSession session = mock(HttpSession.class);
        when(request.getSession()).thenReturn(session);
        when(request.getHeader("uid")).thenReturn("alice");
        when(request.getParameter("redirectUrl")).thenReturn(destination);
        when(request.getContextPath()).thenReturn(HandlerHarness.STANDARD_CONTEXT);

        filter.doFilter(request, response, chain);
    }

    @Test
    public void relativeDestinationIsHonoured() throws Exception {
        HttpServletResponse response = mock(HttpServletResponse.class);
        authenticate("/srv/eng/catalog.search", response, mock(FilterChain.class));
        RedirectProbe probe = RedirectProbe.of(response);
        probe.assertRedirected();
        assertTrue("expected the requested page, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), "/srv/eng/catalog.search"));
    }

    @Test
    public void noDestinationContinuesTheChain() throws Exception {
        HttpServletResponse response = mock(HttpServletResponse.class);
        FilterChain chain = mock(FilterChain.class);
        authenticate(null, response, chain);
        assertNull("no redirect expected when no destination is supplied",
            RedirectProbe.of(response).target());
        verify(chain).doFilter(any(), any());
    }
}
