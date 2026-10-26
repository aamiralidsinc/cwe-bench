package hidden.support;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Attribute;
import org.jsoup.nodes.DataNode;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.Node;
import org.jsoup.safety.Cleaner;
import org.jsoup.safety.Safelist;

import java.util.Locale;

/**
 * Shared assertions for the sanitizer suite. Everything here drives the product's public API and
 * re-checks the returned sanitised markup with the product's own parser: a sanitised document must
 * never contain an element or attribute the configured safelist does not allow.
 */
public final class SanitizerChecks {

    private SanitizerChecks() {}

    public static final String PAYLOAD = "<svg id=PWNMARK onload=alert(1)>x</svg>";

    /** Cleans through both string and document entry points and checks the result. */
    public static void assertNeutralised(String label, String dirty, Safelist safelist) {
        String fromString = Jsoup.clean(dirty, safelist);
        assertNeutral(label + " [clean]", fromString);

        Document parsed = Jsoup.parse(dirty);
        String fromDocument = new Cleaner(safelist).clean(parsed).body().html();
        assertNeutral(label + " [document]", fromDocument);
    }

    /** Asserts that the sanitised markup contains only output the safelist permits. */
    public static void assertNeutral(String label, String sanitised) {
        Document out = Jsoup.parse(sanitised);

        for (Element el : out.select("svg, math, script, object, embed, applet")) {
            throw new AssertionError(label + ": sanitised output reintroduced a disallowed element <"
                + el.tagName() + ">: " + sanitised);
        }

        for (Element el : out.getAllElements()) {
            for (Attribute attr : el.attributes()) {
                String key = attr.getKey().toLowerCase(Locale.ROOT);
                if (key.startsWith("on")) {
                    throw new AssertionError(label + ": sanitised output kept an event-handler attribute "
                        + key + ": " + sanitised);
                }
            }
        }
    }

    /** Asserts that the sanitised output still carries the allowed raw element's text verbatim. */
    public static void assertRawContent(String label, String sanitised, String tag, String expectedContent) {
        Document out = Jsoup.parse(sanitised);
        Element el = out.selectFirst(tag);
        if (el == null)
            throw new AssertionError(label + ": expected a <" + tag + "> element in " + sanitised);
        StringBuilder data = new StringBuilder();
        for (Node node : el.childNodes()) {
            if (node instanceof DataNode)
                data.append(((DataNode) node).getWholeData());
        }
        if (!data.toString().contains(expectedContent)) {
            throw new AssertionError(label + ": expected raw content [" + expectedContent + "] in <" + tag
                + ">, got [" + data + "] from " + sanitised);
        }
    }
}
