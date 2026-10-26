package silverpeas.hidden;

import org.junit.Before;
import org.junit.Test;
import org.silverpeas.web.servlets.OnlineFileServer;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.Assert.assertTrue;

/** A signed-in, entitled user must keep receiving files from the other serving entry point. */
public class FunctionalOnlineFileTest {

  @Before
  public void setUp() {
    Harness.reset();
    Harness.componentFile("comp-a", "legit.txt", "FUNC-ONLINE-ENTITLED-4e19");
    Harness.MEMBER.put("comp-a", true);
  }

  @Test
  public void entitledMemberDownloadsFile() throws Exception {
    Map<String, String> params = new LinkedHashMap<>();
    params.put("ComponentId", "comp-a");
    params.put("SourceFile", "legit.txt");
    params.put("MimeType", "text/plain");
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req = Harness.request("GET", params, session,
        "/OnlineFileServer/legit.txt");
    Harness.Call call = Harness.call(new OnlineFileServer(), req);

    assertTrue("an entitled user could not download a file: " + call.describe(),
        call.bodyContains("FUNC-ONLINE-ENTITLED-4e19"));
  }
}
