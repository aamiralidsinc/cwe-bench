package bench.antisamy;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/** Approved references keep their value and their meaning. */
public class FunctionalUrlTest extends Base {

    @Test
    public void absoluteHrefIsPreserved() throws Exception {
        String input = "<a href=\"https://good.example/page?a=1\">x</a>";
        for (int mode : MODES) {
            assertEquals(modeName(mode) + " changed an approved link",
                    "https://good.example/page?a=1", attribute(scan(input, mode), "href"));
        }
    }

    @Test
    public void relativeHrefIsPreserved() throws Exception {
        String input = "<a href=\"/docs/readme.html\">x</a>";
        for (int mode : MODES) {
            assertEquals(modeName(mode) + " changed an approved relative link",
                    "/docs/readme.html", attribute(scan(input, mode), "href"));
        }
    }

    @Test
    public void backslashRelativeHrefKeepsItsMeaning() throws Exception {
        String input = "<a href=\"docs\\readme.html\">x</a>";
        for (int mode : MODES) {
            String href = attribute(scan(input, mode), "href");
            assertNotNull(modeName(mode) + " dropped an approved relative link", href);
            assertFalse(modeName(mode) + " moved an approved relative link to another origin: " + href,
                    resolvesToAnotherOrigin(href));
            assertTrue(modeName(mode) + " changed the target of an approved relative link: " + href,
                    href.replace('\\', '/').endsWith("docs/readme.html"));
        }
    }
}
