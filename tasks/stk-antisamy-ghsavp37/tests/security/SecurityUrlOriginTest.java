package bench.antisamy;

import org.junit.Test;

import static org.junit.Assert.assertFalse;

/**
 * A reference the policy treats as on-site must never become a reference to another origin
 * once a browser has resolved it.
 */
public class SecurityUrlOriginTest extends Base {

    @Test
    public void backslashProtocolRelativeLinkIsNotEmitted() throws Exception {
        String[] inputs = {
                "<a href=\"/\\evil.example/\">x</a>",
                "<a href=\"\\\\evil.example/\">x</a>",
                "<a href=\"\\\\/evil.example/\">x</a>"
        };
        for (String input : inputs) {
            for (int mode : MODES) {
                String href = attribute(scan(input, mode), "href");
                assertFalse(modeName(mode) + " resolved another origin from " + input + " -> " + href,
                        resolvesToAnotherOrigin(href));
            }
        }
    }

    @Test
    public void backslashProtocolRelativeImageIsNotEmitted() throws Exception {
        String[] inputs = {
                "<img src=\"/\\evil.example/x.png\">",
                "<img src=\"\\\\evil.example/x.png\">"
        };
        for (String input : inputs) {
            for (int mode : MODES) {
                String src = attribute(scan(input, mode), "src");
                assertFalse(modeName(mode) + " resolved another origin from " + input + " -> " + src,
                        resolvesToAnotherOrigin(src));
            }
        }
    }
}
