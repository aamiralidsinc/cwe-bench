package org.fao.geonet.kernel.security.keycloak;

import bench.HandlerHarness;
import bench.RedirectProbe;
import org.junit.After;
import org.junit.Test;
import org.keycloak.KeycloakPrincipal;
import org.keycloak.adapters.RefreshableKeycloakSecurityContext;
import org.keycloak.adapters.spi.KeycloakAccount;
import org.keycloak.adapters.springsecurity.token.KeycloakAuthenticationToken;
import org.keycloak.representations.AccessToken;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.User;
import org.springframework.test.util.ReflectionTestUtils;

import javax.servlet.FilterChain;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * The Keycloak login callback keeps returning the user to an in-application page, and to
 * the application home when no destination is supplied.
 */
public class FunctionalKeycloakRedirectTest {

    @After
    public void clearContext() {
        SecurityContextHolder.clearContext();
    }

    private RedirectProbe completeLogin(String queryString) throws Exception {
        KeycloakUtil.signinPath = "/signin";
        KeycloakAuthenticationProcessingFilter filter =
            new KeycloakAuthenticationProcessingFilter(mock(AuthenticationManager.class));

        KeycloakUserUtils userUtils = mock(KeycloakUserUtils.class);
        ReflectionTestUtils.setField(filter, "keycloakUserUtils", userUtils);
        when(userUtils.getUserDetails(any(), eq(true)))
            .thenReturn(new User("alice", "", AuthorityUtils.NO_AUTHORITIES));

        KeycloakAccount account = mock(KeycloakAccount.class);
        KeycloakPrincipal principal = mock(KeycloakPrincipal.class);
        RefreshableKeycloakSecurityContext securityContext =
            mock(RefreshableKeycloakSecurityContext.class);
        AccessToken token = mock(AccessToken.class);
        when(account.getPrincipal()).thenReturn(principal);
        when(principal.getKeycloakSecurityContext()).thenReturn(securityContext);
        when(securityContext.getToken()).thenReturn(token);

        KeycloakAuthenticationToken authentication = new KeycloakAuthenticationToken(
            account, true, AuthorityUtils.NO_AUTHORITIES);

        HttpServletRequest request = mock(HttpServletRequest.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        when(request.getQueryString()).thenReturn(queryString);
        when(request.getContextPath()).thenReturn(HandlerHarness.STANDARD_CONTEXT);

        filter.successfulAuthentication(request, response, mock(FilterChain.class), authentication);
        return RedirectProbe.of(response);
    }

    @Test
    public void relativeDestinationIsHonoured() throws Exception {
        RedirectProbe probe = completeLogin("redirectUrl=/srv/eng/catalog.search");
        probe.assertRedirected();
        assertTrue("expected the requested page, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), "/srv/eng/catalog.search"));
    }

    @Test
    public void noDestinationUsesContextHome() throws Exception {
        RedirectProbe probe = completeLogin("state=xyz");
        probe.assertRedirected();
        assertTrue("expected the context home, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), "/geonetwork"));
    }
}
