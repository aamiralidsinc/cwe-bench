package org.fao.geonet.kernel.security;

import bench.HandlerHarness;
import bench.RedirectProbe;
import org.junit.After;
import org.junit.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.web.authentication.AuthenticationSuccessHandler;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Form sign-in keeps returning the user to the page they were on, including when that page
 * is supplied as an absolute address on the configured site, and keeps its configured
 * default when no destination is supplied.
 */
public class FunctionalFormLoginRedirectTest {

    @After
    public void tearDown() {
        HandlerHarness.clearContext();
    }


    private RedirectProbe signIn(String destination) throws Exception {
        AuthenticationSuccessHandler handler =
            (AuthenticationSuccessHandler) HandlerHarness.instantiateNestedHandler(
                HandlerHarness.configFile("config-security-core.xml"),
                "formLoginFilter", "authenticationSuccessHandler");

        HttpServletRequest request = mock(HttpServletRequest.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        when(request.getParameter("redirectUrl")).thenReturn(destination);
        when(request.getContextPath()).thenReturn(HandlerHarness.ROOT_CONTEXT);
        when(response.encodeRedirectURL(anyString())).thenAnswer(i -> i.getArgument(0));

        handler.onAuthenticationSuccess(request, response,
            new UsernamePasswordAuthenticationToken("alice", "", AuthorityUtils.NO_AUTHORITIES));
        return RedirectProbe.of(response);
    }

    @Test
    public void relativeDestinationIsHonoured() throws Exception {
        RedirectProbe probe = signIn("/srv/eng/catalog.search");
        probe.assertRedirected();
        assertTrue("expected the requested page, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), "/srv/eng/catalog.search"));
    }

    @Test
    public void absoluteSameSiteDestinationIsHonoured() throws Exception {
        String intended = "https://www.example.org/srv/eng/catalog.search";
        RedirectProbe probe = signIn(intended);
        probe.assertRedirected();
        assertTrue("expected the requested page, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), intended));
    }

    @Test
    public void noDestinationUsesConfiguredDefault() throws Exception {
        RedirectProbe probe = signIn(null);
        probe.assertRedirected();
        assertTrue("expected the configured default, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), "/"));
    }
}
