package org.fao.geonet.kernel.security.keycloak;

import bench.RedirectProbe;
import org.junit.Test;
import org.springframework.security.core.Authentication;
import org.springframework.test.util.ReflectionTestUtils;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * The Keycloak profile's sign-out handler must not pass a request-supplied destination
 * outside the site through to the identity provider's logout URL.
 */
public class SecurityKeycloakLogoutRedirectTest {

    private RedirectProbe signOut(String destination) throws Exception {
        KeycloakConfiguration configuration = mock(KeycloakConfiguration.class);
        when(configuration.getIDPLogoutUrl())
            .thenReturn("https://idp.example.com/logout?redirect={RedirecUrl}");

        KeycloakLogoutSuccessHandler handler = new KeycloakLogoutSuccessHandler();
        ReflectionTestUtils.setField(handler, "keycloakConfiguration", configuration);

        HttpServletRequest request = mock(HttpServletRequest.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        when(request.getRequestURL()).thenReturn(
            new StringBuffer("https://www.example.org/geonetwork/signout"));
        when(request.getRequestURI()).thenReturn("/geonetwork/signout");
        when(request.getContextPath()).thenReturn("/geonetwork");
        when(request.getServerName()).thenReturn("www.example.org");
        when(request.getScheme()).thenReturn("https");
        when(request.getServerPort()).thenReturn(443);
        when(request.getParameter("redirectUrl")).thenReturn(destination);

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
