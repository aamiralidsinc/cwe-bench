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

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * The success handler wired for form sign-in must not hand the browser a destination
 * outside the site.
 */
public class SecurityFormLoginRedirectTest {

    @After
    public void tearDown() {
        HandlerHarness.clearContext();
    }


    private RedirectProbe signIn(String destination, String contextPath) throws Exception {
        AuthenticationSuccessHandler handler =
            (AuthenticationSuccessHandler) HandlerHarness.instantiateNestedHandler(
                HandlerHarness.configFile("config-security-core.xml"),
                "formLoginFilter", "authenticationSuccessHandler");

        HttpServletRequest request = mock(HttpServletRequest.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        when(request.getParameter("redirectUrl")).thenReturn(destination);
        when(request.getContextPath()).thenReturn(contextPath);
        when(response.encodeRedirectURL(anyString())).thenAnswer(i -> i.getArgument(0));

        handler.onAuthenticationSuccess(request, response,
            new UsernamePasswordAuthenticationToken("alice", "", AuthorityUtils.NO_AUTHORITIES));
        return RedirectProbe.of(response);
    }

    @Test
    public void protocolRelativeDestinationIsNotUsed() throws Exception {
        signIn("//attacker.invalid/x", HandlerHarness.ROOT_CONTEXT)
            .assertNotSentTo("attacker.invalid");
    }

    @Test
    public void backslashProtocolRelativeDestinationIsNotUsed() throws Exception {
        signIn("/\\attacker.invalid/x", HandlerHarness.ROOT_CONTEXT)
            .assertNotSentTo("attacker.invalid");
    }

    @Test
    public void absoluteOffSiteDestinationIsNotUsed() throws Exception {
        signIn("https://attacker.invalid/phish", HandlerHarness.STANDARD_CONTEXT)
            .assertNotSentTo("attacker.invalid");
    }
}
