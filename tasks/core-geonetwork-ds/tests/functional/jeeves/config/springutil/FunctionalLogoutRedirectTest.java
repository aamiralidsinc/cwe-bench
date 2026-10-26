package jeeves.config.springutil;

import bench.HandlerHarness;
import bench.RedirectProbe;
import org.fao.geonet.kernel.setting.SettingManager;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.logout.LogoutSuccessHandler;

import javax.servlet.ServletContext;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Sign-out keeps returning the user to the page they were on, including when that page is
 * supplied as an absolute address on the configured site, and keeps its configured
 * default when no destination is supplied.
 */
public class FunctionalLogoutRedirectTest {

    private SettingManager settingManager;
    private ServletContext servletContext;

    @Before
    public void setUp() {
        settingManager = HandlerHarness.settingManager();
        servletContext = HandlerHarness.configureSignOutContext(settingManager);
    }

    @After
    public void tearDown() {
        HandlerHarness.clearContext();
    }

    private RedirectProbe signOut(String destination) throws Exception {
        LogoutSuccessHandler handler = (LogoutSuccessHandler) HandlerHarness.instantiateHandler(
            HandlerHarness.configFile("config-security-core.xml"), "logoutSuccessHandler",
            settingManager, servletContext);

        HttpServletRequest request = mock(HttpServletRequest.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        when(request.getParameter("redirectUrl")).thenReturn(destination);
        when(request.getContextPath()).thenReturn(HandlerHarness.ROOT_CONTEXT);
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
    public void absoluteSameSiteDestinationIsHonoured() throws Exception {
        String intended = "https://www.example.org/srv/eng/catalog.search";
        RedirectProbe probe = signOut(intended);
        probe.assertRedirected();
        assertTrue("expected the requested page, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), intended));
    }

    @Test
    public void noDestinationUsesConfiguredDefault() throws Exception {
        RedirectProbe probe = signOut(null);
        probe.assertRedirected();
        assertTrue("expected the configured default, got " + probe.target(),
            RedirectProbe.sameDestination(probe.target(), "/?node=srv"));
    }
}
