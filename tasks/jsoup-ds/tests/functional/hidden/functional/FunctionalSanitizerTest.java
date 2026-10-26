package hidden.functional;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.parser.ParseSettings;
import org.jsoup.parser.Parser;
import org.jsoup.parser.Tag;
import org.jsoup.parser.TagSet;
import org.jsoup.safety.Cleaner;
import org.jsoup.safety.Safelist;

/**
 * Legitimate sanitizer behaviour that must keep working: allowed raw-text content is preserved
 * verbatim, ordinary cleaning and URL filtering are unchanged, and the public tag/tag-set lookup
 * APIs continue to accept padded and mixed-case names as before.
 */
public class FunctionalSanitizerTest {

    public void testAllowedIframeDataPreserved() {
        Safelist safelist = Safelist.relaxed().addTags("iframe");
        String dirty = "<iframe>content is <data></iframe>";
        String clean = Jsoup.clean(dirty, safelist);
        if (!clean.equals(dirty))
            throw new AssertionError("allowed iframe raw content changed: " + clean);
    }

    public void testAllowedStyleDataPreserved() {
        Safelist safelist = Safelist.relaxed().addTags("style");
        String dirty = "<style>p { color: red; }</style>";
        String clean = Jsoup.clean(dirty, safelist);
        if (!clean.equals(dirty))
            throw new AssertionError("allowed style raw content changed: " + clean);
    }

    public void testNormalSanitization() {
        String clean = Jsoup.clean("<div><b>bold</b><script>alert(1)</script></div>", Safelist.relaxed());
        Document out = Jsoup.parse(clean);
        if (out.select("b").size() != 1)
            throw new AssertionError("allowed <b> removed: " + clean);
        if (!out.select("script").isEmpty())
            throw new AssertionError("disallowed <script> kept: " + clean);
        if (!out.text().equals("bold"))
            throw new AssertionError("unexpected text: " + clean);
    }

    public void testProtocolFiltering() {
        String bad = Jsoup.clean("<a href=\"javascript:alert(1)\">x</a>", Safelist.relaxed());
        if (!Jsoup.parse(bad).select("a").attr("href").isEmpty())
            throw new AssertionError("javascript: href kept: " + bad);

        String good = Jsoup.clean("<a href=\"https://example.com/\">x</a>", Safelist.relaxed());
        if (!Jsoup.parse(good).select("a").attr("href").equals("https://example.com/"))
            throw new AssertionError("https href lost: " + good);
    }

    public void testIsValidSemantics() {
        if (!Jsoup.isValid("<p>ok</p>", Safelist.relaxed()))
            throw new AssertionError("safe input reported invalid");
        if (Jsoup.isValid("<script>alert(1)</script>", Safelist.relaxed()))
            throw new AssertionError("unsafe input reported valid");
    }

    public void testPublicTagLookupTrims() {
        String viaSet = TagSet.Html().valueOf(" p ", Parser.NamespaceHtml).getName();
        if (!viaSet.equals("p"))
            throw new AssertionError("padded tag-set lookup no longer trimmed: [" + viaSet + "]");

        String viaTag = Tag.valueOf(" p ").getName();
        if (!viaTag.equals("p"))
            throw new AssertionError("padded tag lookup no longer trimmed: [" + viaTag + "]");

        String mixed = Tag.valueOf(" P ").getName();
        if (!mixed.equals("P"))
            throw new AssertionError("mixed-case tag lookup no longer trims: [" + mixed + "]");
    }

    public void testCustomDataTagParsing() {
        TagSet tags = TagSet.Html();
        Tag dataTag = tags.valueOf("x-data", Parser.NamespaceHtml);
        dataTag.set(Tag.Data);

        Document doc = Jsoup.parse("<x-data>a < b</x-data>", "", Parser.htmlParser().tagSet(tags));
        Element el = doc.body().child(0);
        if (!el.tagName().equals("x-data") || !el.tag().is(Tag.Data))
            throw new AssertionError("custom data tag lost its identity: " + el.tagName());
        if (!el.html().contains("a < b"))
            throw new AssertionError("custom data content was escaped: " + el.html());
    }

    public void testCustomRcDataTagParsing() {
        TagSet tags = TagSet.Html();
        Tag rcTag = tags.valueOf("x-rc", Parser.NamespaceHtml);
        rcTag.set(Tag.RcData);

        Document doc = Jsoup.parse("<x-rc><b>hi</b></x-rc>", "", Parser.htmlParser().tagSet(tags));
        if (!doc.text().contains("<b>hi</b>"))
            throw new AssertionError("custom rcdata content was not treated as text: " + doc.body().html());
    }

    public void testMixedCaseRcdataEndTag() {
        Document doc = Jsoup.parse("<title><p>Foo</TiTLE>");
        Element title = doc.head().selectFirst("title");
        if (title == null)
            throw new AssertionError("title element missing: " + doc.head().html());
        if (!title.text().equals("<p>Foo"))
            throw new AssertionError("mixed-case rcdata end tag handling changed: [" + title.text() + "]");
    }

    public void testNoscriptFallbackSanitized() {
        String clean = Jsoup.clean("<noscript><p>fallback</p></noscript>", Safelist.relaxed());
        Document out = Jsoup.parse(clean);
        if (out.select("noscript").size() != 0)
            throw new AssertionError("noscript element kept: " + clean);
        if (out.select("p").size() != 1 || !out.select("p").text().equals("fallback"))
            throw new AssertionError("allowed noscript fallback content lost: " + clean);
    }

    public void testPreserveCaseSanitizerKeepsAllowedContent() {
        Parser parser = Parser.htmlParser().settings(ParseSettings.preserveCase);
        Document dirty = Jsoup.parse("<DIV><B>x</B><SCRIPT>y</SCRIPT></DIV>", "", parser);
        String clean = new Cleaner(Safelist.relaxed()).clean(dirty).body().html();
        Document out = Jsoup.parse(clean);
        if (out.select("b").size() != 1 || !out.select("b").text().equals("x"))
            throw new AssertionError("allowed content lost under preserve-case: " + clean);
        if (!out.select("script").isEmpty())
            throw new AssertionError("script kept under preserve-case: " + clean);
    }

    public void testPlainParsingUnaffected() {
        Document doc = Jsoup.parse("<div><p>hi</p></div>");
        Element p = doc.selectFirst("p");
        if (p == null || !p.normalName().equals("p"))
            throw new AssertionError("plain parsing changed: " + doc.body().html());
        if (!doc.body().html().contains("<p>hi</p>"))
            throw new AssertionError("plain markup changed: " + doc.body().html());
    }
}
