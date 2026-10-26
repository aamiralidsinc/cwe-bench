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

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * The Shibboleth pre-authentication handshake must not hand the browser a destination
 * outside the site.
 */
public class SecurityShibbolethRedirectTest {

    @After
    public void tearDown() {
        ApplicationContextHolder.clear();
        SecurityContextHolder.clearContext();
    }

    private RedirectProbe authenticate(String destination) throws Exception {
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
        HttpServletResponse response = mock(HttpServletResponse.class);
        HttpSession session = mock(HttpSession.class);
        when(request.getSession()).thenReturn(session);
        when(request.getHeader("uid")).thenReturn("alice");
        when(request.getParameter("redirectUrl")).thenReturn(destination);
        when(request.getContextPath()).thenReturn(HandlerHarness.STANDARD_CONTEXT);

        filter.doFilter(request, response, mock(FilterChain.class));
        return RedirectProbe.of(response);
    }

    @Test
    public void protocolRelativeDestinationIsNotUsed() throws Exception {
        authenticate("//attacker.invalid/x").assertNotSentTo("attacker.invalid");
    }
}
