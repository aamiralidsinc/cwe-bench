package hidden.security;

import hidden.support.SanitizerChecks;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.parser.Parser;
import org.jsoup.parser.ParseSettings;
import org.jsoup.safety.Cleaner;
import org.jsoup.safety.Safelist;

/**
 * The sanitised result must contain only markup the configured safelist allows. Each case below
 * writes a tag name the safelist does not itself contain, then asks the product to sanitise a
 * document that also carries markup the safelist does not allow. A neutralised result drops that
 * markup; a result that reintroduces it as an element (or as an event-handler attribute) fails.
 */
public class SecuritySanitizerTest {

    private static Safelist allowIframe() {
        return Safelist.relaxed().addTags("iframe");
    }

    private static Safelist allowStyle() {
        return Safelist.relaxed().addTags("style");
    }

    private static Safelist allowXmp() {
        return Safelist.relaxed().addTags("xmp");
    }

    public void testDisguisedIframeInBody() {
        SanitizerChecks.assertNeutralised("iframe control char",
            "<iframe\u001E></iframe>" + SanitizerChecks.PAYLOAD, allowIframe());
    }

    public void testDisguisedIframeUpperCase() {
        SanitizerChecks.assertNeutralised("uppercase iframe control char",
            "<IFRAME\u001E></iframe>" + SanitizerChecks.PAYLOAD, allowIframe());
    }

    public void testDisguisedIframeWithAttributes() {
        SanitizerChecks.assertNeutralised("iframe control char with attributes",
            "<iframe\u001E src=\"about:blank\"></iframe>" + SanitizerChecks.PAYLOAD, allowIframe());
    }

    public void testDisguisedStyleInBody() {
        SanitizerChecks.assertNeutralised("style control char",
            "<style\u001E></style>" + SanitizerChecks.PAYLOAD, allowStyle());
    }

    public void testDisguisedXmpInBody() {
        SanitizerChecks.assertNeutralised("xmp control char",
            "<xmp\u001E></xmp>" + SanitizerChecks.PAYLOAD, allowXmp());
    }

    public void testControlCharacterVariants() {
        char[] controls = {1, 0x0B, 0x1E, 0x1F};
        for (char c : controls) {
            String dirty = "<iframe" + c + "></iframe>" + SanitizerChecks.PAYLOAD;
            SanitizerChecks.assertNeutralised("iframe control char U+" + Integer.toHexString(c), dirty, allowIframe());
        }
    }

    public void testDisguisedInTable() {
        SanitizerChecks.assertNeutralised("iframe control char in table",
            "<table><tr><td><iframe\u001E></iframe>" + SanitizerChecks.PAYLOAD + "</td></tr></table>",
            allowIframe());
    }

    public void testDisguisedInTemplate() {
        SanitizerChecks.assertNeutralised("iframe control char in template",
            "<template><iframe\u001E></iframe>" + SanitizerChecks.PAYLOAD + "</template>", allowIframe());
    }

    public void testCleanerOnParsedDocument() {
        Document dirty = Jsoup.parse("<div><iframe\u001E></iframe>" + SanitizerChecks.PAYLOAD + "</div>");
        String sanitised = new Cleaner(allowIframe()).clean(dirty).body().html();
        SanitizerChecks.assertNeutral("cleaner document control char", sanitised);
    }

    public void testPreserveCaseParsing() {
        Parser parser = Parser.htmlParser().settings(ParseSettings.preserveCase);
        Document dirty = Jsoup.parse("<div><iframe\u001E></iframe>" + SanitizerChecks.PAYLOAD + "</div>", "", parser);
        String sanitised = new Cleaner(allowIframe()).clean(dirty).body().html();
        SanitizerChecks.assertNeutral("cleaner preserve-case control char", sanitised);
    }

    public void testNoscriptIsland() {
        SanitizerChecks.assertNeutralised("noscript island iframe control char",
            "<noscript><iframe\u001E></iframe>" + SanitizerChecks.PAYLOAD + "</noscript>", allowIframe());
    }

    public void testNoscriptIslandNested() {
        SanitizerChecks.assertNeutralised("nested noscript island iframe control char",
            "<div><noscript><iframe\u001E></iframe>" + SanitizerChecks.PAYLOAD + "</noscript></div>", allowIframe());
    }

    public void testNoscriptIslandStyle() {
        SanitizerChecks.assertNeutralised("noscript island style control char",
            "<noscript><style\u001E></style>" + SanitizerChecks.PAYLOAD + "</noscript>", allowStyle());
    }

    public void testDisguisedIframeAtEndOfInput() {
        SanitizerChecks.assertNeutralised("trailing iframe control char",
            "<p>prefix</p><iframe\u001E></iframe>" + SanitizerChecks.PAYLOAD, allowIframe());
    }
}
