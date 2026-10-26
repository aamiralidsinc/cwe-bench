package silverpeas.hidden;

import org.junit.Before;
import org.junit.Test;
import org.silverpeas.web.servlets.FileServer;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * A download request that names no space at all must not be served: the pinned code treats an
 * absent space identifier as a supported "personal space" and resolves the file anyway.
 */
public class SecFileServerComponentGateTest {

  private static final String MARKER = "COMPONENT-GATE-MARKER-7c21";

  @Before
  public void setUp() {
    Harness.reset();
    Harness.componentFile("null", "gate-secret.txt", MARKER);
  }

  @Test
  public void requestWithoutSpaceIdentifierIsRefused() throws Exception {
    HttpSession session = Harness.session("user-1");
    Map<String, String> params = new LinkedHashMap<>();
    params.put("SourceFile", "gate-secret.txt");
    params.put("MimeType", "text/plain");
    HttpServletRequest req = Harness.request("GET", params, session, "/FileServer/gate-secret.txt");
    Harness.Call call = Harness.call(new FileServer(), req);

    assertFalse("the response returned a file served from an unnamed space: " + call.describe(),
        call.bodyContains(MARKER));
    assertTrue("the request was not refused with a client error or a redirect: " + call.describe(),
        call.refused());
  }

  @Test
  public void requestWithoutSpaceIdentifierIsRefusedOnPost() throws Exception {
    HttpSession session = Harness.session("user-1");
    Map<String, String> params = new LinkedHashMap<>();
    params.put("SourceFile", "gate-secret.txt");
    params.put("MimeType", "text/plain");
    HttpServletRequest req = Harness.request("POST", params, session, "/FileServer/gate-secret.txt");
    Harness.Call call = Harness.call(new FileServer(), req);

    assertFalse("the response returned a file served from an unnamed space: " + call.describe(),
        call.bodyContains(MARKER));
    assertTrue("the request was not refused with a client error or a redirect: " + call.describe(),
        call.refused());
  }
}
