package org.fao.geonet.web;

import bench.HandlerHarness;
import bench.RedirectProbe;
import org.junit.Test;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.logout.LogoutSuccessHandler;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * The sign-out success handler of the CAS profile must not hand the browser a destination
 * outside the site. Its configured default target is the external CAS logout URL, which
 * is not a request-supplied destination and must keep working.
 */
public class SecurityCasLogoutRedirectTest {

    private RedirectProbe signOut(String destination) throws Exception {
        LogoutSuccessHandler handler = (LogoutSuccessHandler) HandlerHarness.instantiateHandler(
            HandlerHarness.configFile("config-security-cas.xml"), "logoutSuccessHandler",
            HandlerHarness.settingManager(), null);

        HttpServletRequest request = mock(HttpServletRequest.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        when(request.getParameter("redirect")).thenReturn(destination);
        when(request.getContextPath()).thenReturn(HandlerHarness.ROOT_CONTEXT);
        when(response.encodeRedirectURL(anyString())).thenAnswer(i -> i.getArgument(0));

        handler.onLogoutSuccess(request, response, mock(Authentication.class));
        return RedirectProbe.of(response);
    }

    @Test
    public void absoluteOffSiteDestinationIsNotUsed() throws Exception {
        signOut("https://attacker.invalid/phish").assertNotSentTo("attacker.invalid");
    }

    @Test
    public void protocolRelativeDestinationIsNotUsed() throws Exception {
        signOut("//attacker.invalid/x").assertNotSentTo("attacker.invalid");
    }

    @Test
    public void backslashProtocolRelativeDestinationIsNotUsed() throws Exception {
        signOut("/\\attacker.invalid/x").assertNotSentTo("attacker.invalid");
    }
}
