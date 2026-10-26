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

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * The sign-out success handler must not hand the browser a destination outside the site.
 */
public class SecurityLogoutRedirectTest {

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
    public void protocolRelativeDestinationIsNotUsed() throws Exception {
        signOut("//attacker.invalid/x").assertNotSentTo("attacker.invalid");
    }

    @Test
    public void backslashProtocolRelativeDestinationIsNotUsed() throws Exception {
        signOut("/\\attacker.invalid/x").assertNotSentTo("attacker.invalid");
    }
}
