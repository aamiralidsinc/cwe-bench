package org.fao.geonet.kernel.security.openidconnect;

import bench.HandlerHarness;
import bench.RedirectProbe;
import org.junit.After;
import org.junit.Test;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
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
 * The OIDC login callback keeps returning the user to an in-application page, and to the
 * application home when no destination is supplied.
 */
public class FunctionalOidcRedirectTest {

    @After
    public void clearContext() {
        SecurityContextHolder.clearContext();
    }

    private RedirectProbe completeLogin(String queryString) throws Exception {
        GeonetworkOAuth2LoginAuthenticationFilter filter =
            new GeonetworkOAuth2LoginAuthenticationFilter(
                mock(ClientRegistrationRepository.class),
                mock(OAuth2AuthorizedClientService.class));

        OAuth2SecurityProviderUtil providerUtil = mock(OAuth2SecurityProviderUtil.class);
        ReflectionTestUtils.setField(filter, "oAuth2SecurityProviderUtil", providerUtil);
        when(providerUtil.getUserDetails(any(), eq(true)))
            .thenReturn(new User("alice", "", AuthorityUtils.NO_AUTHORITIES));

        OidcUser oidcUser = mock(OidcUser.class);
        OAuth2AuthenticationToken authentication = new OAuth2AuthenticationToken(
            oidcUser, AuthorityUtils.NO_AUTHORITIES, "geonetwork");

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
