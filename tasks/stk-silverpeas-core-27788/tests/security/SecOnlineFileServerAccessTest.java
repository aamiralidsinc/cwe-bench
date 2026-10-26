package silverpeas.hidden;

import org.junit.Before;
import org.junit.Test;
import org.silverpeas.web.servlets.OnlineFileServer;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * The other file-serving entry point reaches the same store. A caller must be signed in and
 * entitled to the space the file belongs to before any content is returned.
 */
public class SecOnlineFileServerAccessTest {

  private static final String MARKER = "ONLINE-ACCESS-MARKER-51d0";

  @Before
  public void setUp() {
    Harness.reset();
    Harness.componentFile("comp-a", "shared.txt", MARKER);
    Harness.componentFile("null", "unscoped.txt", MARKER);
  }

  private Map<String, String> params(String componentId, String source) {
    Map<String, String> params = new LinkedHashMap<>();
    if (componentId != null) {
      params.put("ComponentId", componentId);
    }
    params.put("SourceFile", source);
    params.put("MimeType", "text/plain");
    return params;
  }

  @Test
  public void anonymousCallerIsRefused() throws Exception {
    Harness.MEMBER.put("comp-a", true);
    HttpServletRequest req = Harness.request("GET", params("comp-a", "shared.txt"), null,
        "/OnlineFileServer/shared.txt");
    Harness.Call call = Harness.call(new OnlineFileServer(), req);

    assertFalse("an anonymous caller received a component file: " + call.describe(),
        call.bodyContains(MARKER));
    assertTrue("the request was not refused with a client error or a redirect: " + call.describe(),
        call.refused());
  }

  @Test
  public void callerWithoutEntitlementIsRefused() throws Exception {
    Harness.MEMBER.put("comp-a", false);
    Harness.MEMBER.put("comp-other", true);
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req = Harness.request("GET", params("comp-a", "shared.txt"), session,
        "/OnlineFileServer/shared.txt");
    Harness.Call call = Harness.call(new OnlineFileServer(), req);

    assertFalse("a caller not entitled to the space received its file: " + call.describe(),
        call.bodyContains(MARKER));
    assertTrue("the request was not refused with a client error or a redirect: " + call.describe(),
        call.refused());
  }

  @Test
  public void requestWithoutSpaceIdentifierIsRefused() throws Exception {
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req = Harness.request("GET", params(null, "unscoped.txt"), session,
        "/OnlineFileServer/unscoped.txt");
    Harness.Call call = Harness.call(new OnlineFileServer(), req);

    assertFalse("the response returned a file served from an unnamed space: " + call.describe(),
        call.bodyContains(MARKER));
    assertTrue("the request was not refused with a client error or a redirect: " + call.describe(),
        call.refused());
  }
}
