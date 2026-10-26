package silverpeas.hidden;

import org.junit.Before;
import org.junit.Test;
import org.silverpeas.web.servlets.FileServer;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.Assert.assertTrue;

/** Ordinary downloads that must keep working exactly as they do today. */
public class FunctionalFileAccessTest {

  @Before
  public void setUp() {
    Harness.reset();
  }

  private Map<String, String> params() {
    Map<String, String> params = new LinkedHashMap<>();
    params.put("ComponentId", "comp-a");
    params.put("MimeType", "text/plain");
    return params;
  }

  @Test
  public void memberDownloadsComponentFile() throws Exception {
    String marker = "FUNC-PLAIN-2ac1";
    Harness.componentFile("comp-a", "document.txt", marker);
    Harness.MEMBER.put("comp-a", true);

    Map<String, String> params = params();
    params.put("SourceFile", "document.txt");
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req = Harness.request("GET", params, session, "/FileServer/document.txt");
    Harness.Call call = Harness.call(new FileServer(), req);

    assertTrue("a member could not download a file of their space: " + call.describe(),
        call.bodyContains(marker));
  }

  @Test
  public void storageSpaceSharesFileWithNonMember() throws Exception {
    String marker = "FUNC-STORAGE-6db8";
    Harness.componentFile("comp-a", "shared-document.txt", marker);
    Harness.MEMBER.put("comp-a", false);
    Harness.PUBLIC_FILES.put("comp-a", "yes");

    Map<String, String> params = params();
    params.put("SourceFile", "shared-document.txt");
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req =
        Harness.request("GET", params, session, "/FileServer/shared-document.txt");
    Harness.Call call = Harness.call(new FileServer(), req);

    assertTrue("a user of a storage space could not download its shared file: " + call.describe(),
        call.bodyContains(marker));
  }

  @Test
  public void resizedImagePathIsServed() throws Exception {
    String marker = "FUNC-THUMBNAIL-f04e";
    Harness.componentFile("comp-a", "100x100/photo.png", marker);
    Harness.MEMBER.put("comp-a", true);

    Map<String, String> params = params();
    params.put("SourceFile", "photo.png");
    params.put("Size", "100x100");
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req = Harness.request("GET", params, session, "/FileServer/photo.png");
    Harness.Call call = Harness.call(new FileServer(), req);

    assertTrue("a resized image was not served: " + call.describe(),
        call.bodyContains(marker));
  }

  @Test
  public void nestedDirectoryIsServed() throws Exception {
    String marker = "FUNC-NESTED-8a37";
    Harness.componentFile("comp-a", "sub/dir/deep.txt", marker);
    Harness.MEMBER.put("comp-a", true);

    Map<String, String> params = params();
    params.put("SourceFile", "deep.txt");
    params.put("Directory", "sub/dir");
    HttpSession session = Harness.session("user-1");
    HttpServletRequest req = Harness.request("GET", params, session, "/FileServer/deep.txt");
    Harness.Call call = Harness.call(new FileServer(), req);

    assertTrue("a file in a nested directory was not served: " + call.describe(),
        call.bodyContains(marker));
  }
}
