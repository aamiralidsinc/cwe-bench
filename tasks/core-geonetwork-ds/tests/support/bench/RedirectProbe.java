package bench;

import org.mockito.Mockito;
import org.mockito.invocation.Invocation;

import javax.servlet.http.HttpServletResponse;
import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;

import static org.junit.Assert.fail;

/**
 * Captures what a handler actually told the servlet response to do, and provides the
 * product-neutral checks the suites use: "was the browser sent to this host?" and
 * "does the redirect land on this intended page?".
 *
 * <p>Expected values are computed here from the test input; no product helper is used.</p>
 */
public final class RedirectProbe {

    private String redirect;
    private String locationHeader;
    private Integer status;
    private String errorMessage;

    public static RedirectProbe of(HttpServletResponse response) {
        RedirectProbe p = new RedirectProbe();
        for (Invocation inv : Mockito.mockingDetails(response).getInvocations()) {
            String name = inv.getMethod().getName();
            Object[] args = inv.getArguments();
            if ("sendRedirect".equals(name) && args.length == 1) {
                p.redirect = (String) args[0];
            } else if ("sendError".equals(name) && args.length >= 1) {
                p.status = (Integer) args[0];
                if (args.length > 1) {
                    p.errorMessage = (String) args[1];
                }
            } else if ("setStatus".equals(name) && args.length == 1) {
                p.status = (Integer) args[0];
            } else if (("setHeader".equals(name) || "addHeader".equals(name))
                && args.length == 2 && "Location".equalsIgnoreCase((String) args[0])) {
                p.locationHeader = (String) args[1];
            }
        }
        return p;
    }

    public String target() {
        return redirect != null ? redirect : locationHeader;
    }

    public int status() {
        return status == null ? 200 : status;
    }

    public boolean refused() {
        return status != null && status >= 400 && status < 500 && target() == null;
    }

    public String errorMessage() {
        return errorMessage;
    }

    /** True when this response hands the browser a destination that belongs to {@code host}. */
    public boolean mentionsHost(String host) {
        String needle = host.toLowerCase();
        String t = target();
        if (t != null) {
            String raw = t.toLowerCase();
            String decoded = decode(t).toLowerCase();
            if (raw.contains(needle) || decoded.contains(needle)) {
                return true;
            }
            if (targetHost(t).equals(needle)) {
                return true;
            }
        }
        if (errorMessage != null && decode(errorMessage).toLowerCase().contains(needle)) {
            return true;
        }
        return false;
    }

    public void assertNotSentTo(String host) {
        if (status != null && status >= 500) {
            fail("the application failed with a server error instead of refusing the request: "
                + status);
        }
        if (refused()) {
            return;
        }
        if (mentionsHost(host)) {
            fail("the response sent the browser to the off-site destination: " + target());
        }
    }

    public void assertRedirected() {
        if (target() == null) {
            fail("expected a redirect but the response had none (status " + status() + ")");
        }
        if (target().isEmpty()) {
            fail("expected a non-empty redirect destination");
        }
    }

    /**
     * True when {@code actual} lands the user on the same site and page as
     * {@code intended}. {@code intended} may be an absolute same-site address or a path;
     * {@code actual} may be the same absolute address, a context-relative form of it, or
     * the path itself (as produced by the product's redirect strategy).
     */
    public static boolean sameDestination(String actual, String intended) {
        if (actual == null || intended == null) {
            return false;
        }
        String a = actual.replace('\\', '/');
        if (a.startsWith("//")) {
            return false;
        }
        String intendedPath = pathOf(intended);
        String actualPath = pathOf(a);
        if (actualPath.equals(intendedPath)) {
            return true;
        }
        // The strategy may add the deployment context to a site path.
        return intendedPath.startsWith("/") && !intendedPath.equals("/")
            && actualPath.endsWith(intendedPath);
    }

    /** Path plus query, ignoring scheme/host/port. */
    private static String pathOf(String url) {
        String u = url.replace('\\', '/');
        int scheme = u.indexOf("://");
        if (scheme > 0) {
            int slash = u.indexOf('/', scheme + 3);
            return slash < 0 ? "/" : u.substring(slash);
        }
        return u;
    }

    public static String decode(String value) {
        try {
            // '+' is a literal plus in a redirect target, not a space.
            return URLDecoder.decode(value.replace("+", "%2B"), "UTF-8");
        } catch (UnsupportedEncodingException | IllegalArgumentException e) {
            return value;
        }
    }

    /** Host part of a redirect target, or "" when it is a path. */
    public static String targetHost(String url) {
        if (url == null) {
            return "";
        }
        String u = url.replace('\\', '/');
        String authority = null;
        if (u.startsWith("//")) {
            authority = u.substring(2);
        } else {
            int scheme = u.indexOf("://");
            if (scheme > 0 && u.substring(0, scheme).matches("[a-zA-Z][a-zA-Z0-9+.-]*")) {
                authority = u.substring(scheme + 3);
            }
        }
        if (authority == null) {
            return "";
        }
        int end = authority.length();
        for (int i = 0; i < authority.length(); i++) {
            char c = authority.charAt(i);
            if (c == '/' || c == '?' || c == '#') {
                end = i;
                break;
            }
        }
        authority = authority.substring(0, end);
        int at = authority.lastIndexOf('@');
        if (at >= 0) {
            authority = authority.substring(at + 1);
        }
        if (authority.startsWith("[")) {
            int close = authority.indexOf(']');
            return close > 0 ? authority.substring(0, close + 1).toLowerCase() : authority.toLowerCase();
        }
        int colon = authority.lastIndexOf(':');
        if (colon >= 0) {
            authority = authority.substring(0, colon);
        }
        return authority.toLowerCase();
    }
}
