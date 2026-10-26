package silverpeas.hidden;

import org.junit.Before;
import org.junit.Test;
import org.silverpeas.web.servlets.FileServer;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;
import java.io.File;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * A caller who is entitled to one space must not obtain a file outside that space by supplying
 * an absolute location in the download request.
 */
public class SecFileServerAbsolutePathTest {

  private static final String MARKER = "ABSOLUTE-PATH-MARKER-93af";

  @Before
  public void setUp() {
    Harness.reset();
    Harness.MEMBER.put("comp-a", true);
  }

  private Map<String, String> attack() {
    File outside = Harness.outsideFile("outside-secret.txt", MARKER);
    Map<String, String> params = new LinkedHashMap<>();
    params.put("ComponentId", "comp-a");
    params.put("SourceFile", outside.getAbsolutePath());
    params.put("MimeType", "text/plain");
    params.put("TypeUpload", "1");
    return params;
  }

  @Test
  public void absoluteSourceIsNotServed() throws Exception {
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req =
        Harness.request("GET", attack(), session, "/FileServer/outside-secret.txt");
    Harness.Call call = Harness.call(new FileServer(), req);

    assertFalse("the response returned a file located outside the entitled space: "
        + call.describe(), call.bodyContains(MARKER));
    assertTrue("the request was not refused with a client error or a redirect: " + call.describe(),
        call.refused());
  }

  @Test
  public void absoluteSourceIsNotServedOnPost() throws Exception {
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req =
        Harness.request("POST", attack(), session, "/FileServer/outside-secret.txt");
    Harness.Call call = Harness.call(new FileServer(), req);

    assertFalse("the response returned a file located outside the entitled space: "
        + call.describe(), call.bodyContains(MARKER));
    assertTrue("the request was not refused with a client error or a redirect: " + call.describe(),
        call.refused());
  }
}
