package silverpeas.hidden;

import org.junit.Before;
import org.junit.Test;
import org.silverpeas.web.servlets.TempFileServer;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;

import static org.junit.Assert.assertTrue;

/** Temporary files with a nested path and a non-ASCII name must keep downloading. */
public class FunctionalTempFileTest {

  @Before
  public void setUp() {
    Harness.reset();
  }

  @Test
  public void nestedAndAccentedTempFileIsServed() throws Exception {
    String marker = "FUNC-TEMP-ACCENT-31b6";
    Harness.temporaryFile("subdir/rapport final é.txt", marker);
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req = Harness.request("GET", new java.util.LinkedHashMap<>(),
        session, "/subdir/rapport%20final%20%C3%A9.txt");
    Harness.Call call = Harness.call(new TempFileServer(), req);

    assertTrue("a nested temporary file with an accented name was not served: "
        + call.describe(), call.bodyContains(marker));
  }

  @Test
  public void plainTempFileIsServed() throws Exception {
    String marker = "FUNC-TEMP-PLAIN-77c4";
    Harness.temporaryFile("export.csv", marker);
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req = Harness.request("GET", new java.util.LinkedHashMap<>(),
        session, "/export.csv");
    Harness.Call call = Harness.call(new TempFileServer(), req);

    assertTrue("a temporary file was not served: " + call.describe(),
        call.bodyContains(marker));
  }
}
