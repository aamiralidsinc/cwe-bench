package org.fao.geonet.web;

import bench.HandlerHarness;
import bench.RedirectProbe;
import org.junit.Test;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.logout.LogoutSuccessHandler;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * The CAS profile's sign-out keeps honouring an in-application destination and keeps its
 * configured external CAS logout target when none is supplied.
 */
public class FunctionalCasLogoutRedirectTest {

    private static final String CAS_DEFAULT =
        "https://cas.example.com/logout?url=https://www.example.org/geonetwork/";

    private RedirectProbe signOut(String destination) throws Exception {
        LogoutSuccessHandler handler = (LogoutSuccessHandler) HandlerHarness.instantiateHandler(
            HandlerHarness.configFile("config-security-cas.xml"), "logoutSuccessHandler",
            HandlerHarness.settingManager(), null);

        HttpServletRequest request = mock(HttpServletRequest.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        when(request.getParameter("redirect")).thenReturn(destination);
        when(request.getContextPath()).thenReturn(HandlerHarness.STANDARD_CONTEXT);
        when(response.encodeRedirectURL(anyString())).thenAnswer(i -> i.getArgument(0));

        handler.onLogoutSuccess(request, response, mock(Authentication.class));
        return RedirectProbe.of(response);
    }

    @Test
    public void relativeDestinationIsHonoured() throws Exception {
        RedirectProbe probe = signOut("/srv/eng/catalog.search");
        probe.assertRedirected();
        assertTrue("expected the requested page, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), "/srv/eng/catalog.search"));
    }

    @Test
    public void noDestinationUsesConfiguredDefault() throws Exception {
        RedirectProbe probe = signOut(null);
        assertEquals(CAS_DEFAULT, probe.target());
    }
}
