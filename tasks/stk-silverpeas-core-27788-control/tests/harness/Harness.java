package silverpeas.hidden;

import org.mockito.stubbing.Answer;
import org.silverpeas.core.admin.service.OrganizationController;
import org.silverpeas.core.admin.user.model.User;
import org.silverpeas.core.admin.user.model.UserDetail;
import org.silverpeas.core.admin.user.service.UserProvider;
import org.silverpeas.core.io.file.FileExistenceCheckingProcessor;
import org.silverpeas.core.io.file.RelativePathCheckingProcessor;
import org.silverpeas.core.security.authorization.ComponentAccessControl;
import org.silverpeas.core.web.mvc.controller.MainSessionController;
import org.silverpeas.core.web.mvc.controller.SilverpeasWebUtil;
import org.silverpeas.kernel.BeanContainer;
import org.silverpeas.kernel.test.TestBeanContainer;

import javax.servlet.RequestDispatcher;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;
import java.io.File;
import java.io.IOException;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Map;
import java.util.ServiceLoader;
import java.util.concurrent.ConcurrentHashMap;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Small in-process harness: drives the real servlet entry points with ordinary servlet requests
 * and a fake response, and supplies the product's own authorization services with per-resource
 * answers, exactly like the production beans do.
 */
public final class Harness {

  public static final File WORK = new File(System.getProperty("hidden.work", "/tmp/silverpeas-hidden"));
  public static final File UPLOADS = new File(WORK, "uploads");
  public static final File TEMP = new File(WORK, "temp");
  public static final File OUTSIDE = new File(WORK, "outside");

  /** componentId -> is the current user a member (the component is available to them). */
  public static final Map<String, Boolean> MEMBER = new ConcurrentHashMap<>();
  /** componentId -> value of the component parameter "publicFiles". */
  public static final Map<String, String> PUBLIC_FILES = new ConcurrentHashMap<>();

  private static final OrganizationController ORG = mock(OrganizationController.class);
  private static final ComponentAccessControl CAC = mock(ComponentAccessControl.class);
  private static final UserProvider USERS = mock(UserProvider.class);
  private static final java.util.concurrent.atomic.AtomicReference<User> CURRENT =
      new java.util.concurrent.atomic.AtomicReference<>();
  private static boolean beansReady;

  private Harness() {
  }

  /** Fresh fixture tree and fresh authorization answers for one test. */
  public static void reset() {
    delete(WORK);
    mkdirs(UPLOADS);
    mkdirs(TEMP);
    mkdirs(OUTSIDE);
    MEMBER.clear();
    PUBLIC_FILES.clear();
    initBeans();
    registerProcessors();
  }

  private static synchronized void initBeans() {
    if (beansReady) {
      return;
    }
    when(ORG.isComponentAvailableToUser(anyString(), anyString()))
        .thenAnswer(inv -> Boolean.TRUE.equals(MEMBER.get(inv.getArgument(0))));
    when(CAC.isUserAuthorized(anyString(), anyString()))
        .thenAnswer(inv -> Boolean.TRUE.equals(MEMBER.get(inv.getArgument(1))));
    when(CAC.isUserAuthorized(anyString(), anyString(), any()))
        .thenAnswer(inv -> Boolean.TRUE.equals(MEMBER.get(inv.getArgument(1))));
    when(USERS.getCurrentRequester()).thenAnswer(inv -> CURRENT.get());
    when(USERS.getUser(anyString())).thenAnswer(inv -> user(inv.getArgument(0)));
    TestBeanContainer container = container();
    container.putBean(ORG, OrganizationController.class);
    container.putBean(CAC, ComponentAccessControl.class);
    container.putBean(USERS, UserProvider.class);
    beansReady = true;
  }

  private static User user(String id) {
    if (id == null) {
      return null;
    }
    User user = mock(User.class);
    when(user.getId()).thenReturn(id);
    when(user.isValidState()).thenReturn(true);
    return user;
  }

  private static TestBeanContainer container() {
    // Use the very container instance the product's service provider holds: a second
    // ServiceLoader lookup would give a new, empty TestBeanContainer instance.
    BeanContainer found;
    try {
      org.silverpeas.kernel.ManagedBeanProvider provider =
          org.silverpeas.kernel.ManagedBeanProvider.getInstance();
      java.lang.reflect.Method accessor =
          org.silverpeas.kernel.ManagedBeanProvider.class.getDeclaredMethod("beanContainer");
      accessor.setAccessible(true);
      found = (BeanContainer) accessor.invoke(provider);
    } catch (ReflectiveOperationException e) {
      found = ServiceLoader.load(BeanContainer.class).findFirst()
          .orElseThrow(() -> new IllegalStateException("no bean container for the harness"));
    }
    if (!(found instanceof TestBeanContainer)) {
      throw new IllegalStateException("the harness needs the test bean container, got " + found);
    }
    return (TestBeanContainer) found;
  }

  private static void registerProcessors() {
    if (processorsReady) {
      return;
    }
    try {
      new RelativePathCheckingProcessor().init();
      new FileExistenceCheckingProcessor().init();
    } finally {
      processorsReady = true;
    }
  }

  private static boolean processorsReady;

  /** The current user; the session and the authorization services all answer for this id. */
  public static HttpSession session(String userId) {
    MainSessionController controller = mock(MainSessionController.class);
    UserDetail detail = mock(UserDetail.class);
    when(detail.isValidState()).thenReturn(true);
    when(detail.getId()).thenReturn(userId);
    when(controller.getUserId()).thenReturn(userId);
    when(controller.getSessionId()).thenReturn("session-" + userId);
    when(controller.getCurrentUserDetail()).thenReturn(detail);
    when(controller.getComponentParameterValue(anyString(), anyString()))
        .thenAnswer(inv -> "publicFiles".equals(inv.getArgument(1))
            ? PUBLIC_FILES.get(inv.getArgument(0)) : null);

    HttpSession session = mock(HttpSession.class);
    when(session.getId()).thenReturn("session-" + userId);
    when(session.getAttribute(MainSessionController.MAIN_SESSION_CONTROLLER_ATT))
        .thenReturn(controller);
    return session;
  }

  /** Builds a request whose parameters are simple string values (null omits the parameter). */
  public static HttpServletRequest request(String method, Map<String, String> params,
      HttpSession session, String pathInfo) {
    Map<String, String[]> map = new HashMap<>();
    for (Map.Entry<String, String> e : params.entrySet()) {
      if (e.getValue() != null) {
        map.put(e.getKey(), new String[]{e.getValue()});
      }
    }
    if (session == null) {
      CURRENT.set(null);
    } else {
      MainSessionController controller = (MainSessionController) session.getAttribute(
          MainSessionController.MAIN_SESSION_CONTROLLER_ATT);
      CURRENT.set(user(controller == null ? null : controller.getUserId()));
    }
    HttpServletRequest req = mock(HttpServletRequest.class);
    when(req.getParameterMap()).thenReturn(map);
    when(req.getParameter(anyString())).thenAnswer(inv -> {
      String[] v = map.get(inv.getArgument(0));
      return v == null ? null : v[0];
    });
    when(req.getMethod()).thenReturn(method);
    when(req.getRequestURI()).thenReturn("/silverpeas" + (pathInfo == null ? "/" : pathInfo));
    when(req.getContextPath()).thenReturn("");
    when(req.getPathInfo()).thenReturn(pathInfo);
    when(req.getSession()).thenReturn(session);
    when(req.getSession(true)).thenReturn(session);
    when(req.getSession(false)).thenReturn(session);
    when(req.getHeader(anyString())).thenReturn(null);
    RequestDispatcher dispatcher = mock(RequestDispatcher.class);
    when(req.getRequestDispatcher(anyString())).thenReturn(dispatcher);
    try {
      org.mockito.Mockito.doAnswer(inv -> {
        Object res = inv.getArgument(1);
        if (res instanceof FakeResponse) {
          ((FakeResponse) res).markForwarded();
        }
        return null;
      }).when(dispatcher).forward(any(), any());
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
    return req;
  }

  /** Runs the servlet's real entry point and returns what the client would have seen. */
  public static Call call(HttpServlet servlet, HttpServletRequest request) {
    inject(servlet, request);
    FakeResponse response = new FakeResponse();
    try {
      // Servlet.service(ServletRequest, ServletResponse) is the public entry point; the
      // HttpServletRequest overload is protected.
      javax.servlet.Servlet api = servlet;
      api.service(request, response);
    } catch (Throwable t) {
      response.setThrown(t);
    }
    return new Call(response);
  }

  private static void inject(HttpServlet servlet, HttpServletRequest request) {
    SilverpeasWebUtil webUtil = mock(SilverpeasWebUtil.class);
    when(webUtil.getMainSessionController(any(HttpServletRequest.class)))
        .thenAnswer(inv -> {
          HttpServletRequest r = inv.getArgument(0);
          HttpSession s = r.getSession(false);
          return s == null ? null
              : (MainSessionController) s.getAttribute(MainSessionController.MAIN_SESSION_CONTROLLER_ATT);
        });
    for (Class<?> c = servlet.getClass(); c != null && c != Object.class; c = c.getSuperclass()) {
      for (Field f : c.getDeclaredFields()) {
        Object value = null;
        if (OrganizationController.class.isAssignableFrom(f.getType())
            && f.getType().isInstance(ORG)) {
          value = ORG;
        } else if (ComponentAccessControl.class.isAssignableFrom(f.getType())
            && f.getType().isInstance(CAC)) {
          value = CAC;
        } else if (f.getType().equals(SilverpeasWebUtil.class)) {
          value = webUtil;
        }
        if (value != null) {
          try {
            f.setAccessible(true);
            f.set(servlet, value);
          } catch (ReflectiveOperationException ignored) {
            // a field the servlet does not use; the static service lookups still answer.
          }
        }
      }
    }
  }

  public static File componentFile(String componentId, String relativePath, String content) {
    return write(new File(new File(UPLOADS, componentId), relativePath), content);
  }

  public static File temporaryFile(String relativePath, String content) {
    return write(new File(TEMP, relativePath), content);
  }

  public static File outsideFile(String name, String content) {
    return write(new File(OUTSIDE, name), content);
  }

  private static File write(File file, String content) {
    try {
      mkdirs(file.getParentFile());
      Files.write(file.toPath(), content.getBytes(StandardCharsets.UTF_8));
      return file;
    } catch (IOException e) {
      throw new IllegalStateException(e);
    }
  }

  private static void mkdirs(File dir) {
    if (dir != null && !dir.isDirectory() && !dir.mkdirs()) {
      throw new IllegalStateException("cannot create " + dir);
    }
  }

  private static void delete(File file) {
    if (file == null || !file.exists()) {
      return;
    }
    File[] children = file.listFiles();
    if (children != null) {
      for (File child : children) {
        delete(child);
      }
    }
    //noinspection ResultOfMethodCallIgnored
    file.delete();
  }

  /** What the client received. */
  public static final class Call {
    private final FakeResponse response;

    Call(FakeResponse response) {
      this.response = response;
    }

    public int status() {
      return response.status();
    }

    public boolean bodyContains(String marker) {
      return response.body().contains(marker);
    }

    public boolean redirected() {
      return response.redirect() != null;
    }

    public boolean forwarded() {
      return response.isForwarded();
    }

    /** True only for a deliberate refusal: a client error, a redirect or a forward. */
    public boolean refused() {
      return status() >= 400 || redirected() || forwarded();
    }

    public Throwable thrown() {
      return response.thrown();
    }

    public String describe() {
      String body = response.body();
      if (body.length() > 200) {
        body = body.substring(0, 200) + "...";
      }
      return "status=" + status() + (redirected() ? " redirect=" + response.redirect() : "")
          + (forwarded() ? " forwarded" : "") + (response.thrown() != null
          ? " thrown=" + response.thrown().getClass().getName() : "") + " body=[" + body + "]";
    }
  }
}
