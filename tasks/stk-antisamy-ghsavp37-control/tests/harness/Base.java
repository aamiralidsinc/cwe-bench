package bench.antisamy;

import org.owasp.validator.html.AntiSamy;
import org.owasp.validator.html.Policy;
import org.owasp.validator.html.PolicyException;
import org.owasp.validator.html.ScanException;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Shared, product-independent bookkeeping for the hidden suites. Expected values are computed
 * here with plain Java; only the public scan API is used.
 */
public abstract class Base {

    protected static final int[] MODES = {AntiSamy.DOM, AntiSamy.SAX};

    private static final Policy POLICY = loadPolicy();

    private static Policy loadPolicy() {
        try {
            return Policy.getInstance(Base.class.getResource("/antisamy.xml"));
        } catch (Exception e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    protected static String scan(String input, int mode) throws ScanException, PolicyException {
        return new AntiSamy().scan(input, POLICY, mode).getCleanHTML();
    }

    protected static String scanWithDirective(String input, int mode, String name, String value)
            throws ScanException, PolicyException {
        return new AntiSamy().scan(input, POLICY.cloneWithDirective(name, value), mode).getCleanHTML();
    }

    protected static String modeName(int mode) {
        return mode == AntiSamy.DOM ? "DOM" : "SAX";
    }

    /** First value of the named attribute in the cleaned markup, or null when absent. */
    protected static String attribute(String markup, String name) {
        Matcher m = Pattern.compile("(?is)\\b" + Pattern.quote(name) + "\\s*=\\s*\"([^\"]*)\"")
                .matcher(markup);
        return m.find() ? m.group(1) : null;
    }

    /**
     * True when a browser would resolve the value as a reference to another origin: a
     * protocol-relative reference after the browser's own normalisation of separators.
     */
    protected static boolean resolvesToAnotherOrigin(String url) {
        if (url == null) {
            return false;
        }
        String normalised = url.replace('\\', '/').trim();
        return normalised.startsWith("//");
    }

    /** True when the cleaned markup emits the given element in self-closing form. */
    protected static boolean isSelfClosed(String markup, String tag) {
        return Pattern.compile("(?is)<" + Pattern.quote(tag) + "\\b[^>]*?/>").matcher(markup).find();
    }

    /** What a client-supplied fragment must never smuggle into the cleaned output. */
    protected static void assertNoExecutableContent(String where, String cleaned) {
        String lower = cleaned.toLowerCase();
        if (lower.contains("javascript:")) {
            throw new AssertionError(where + ": the cleaned output carries a javascript: value: " + cleaned);
        }
        if (lower.contains("<script")) {
            throw new AssertionError(where + ": the cleaned output carries a script element: " + cleaned);
        }
        if (Pattern.compile("(?i)\\bon[a-z]{3,}\\s*=").matcher(cleaned).find()) {
            throw new AssertionError(where + ": the cleaned output carries an event handler: " + cleaned);
        }
    }
}
