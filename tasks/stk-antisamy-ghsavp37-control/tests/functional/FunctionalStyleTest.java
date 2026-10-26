package bench.antisamy;

import org.junit.Test;

import static org.junit.Assert.assertTrue;

/** Stylesheets and inline styles the policy allows keep working. */
public class FunctionalStyleTest extends Base {

    @Test
    public void legitimateStyleSheetIsPreserved() throws Exception {
        for (int mode : MODES) {
            String out = scan("<style>a{color:red;font-weight:bold}</style>", mode).toLowerCase();
            assertTrue(modeName(mode) + " dropped the style element: " + out, out.contains("<style"));
            assertTrue(modeName(mode) + " dropped a colour declaration: " + out, out.contains("color"));
            assertTrue(modeName(mode) + " dropped the colour value: " + out, out.contains("red"));
            assertTrue(modeName(mode) + " dropped a weight declaration: " + out, out.contains("font-weight"));
        }
    }

    @Test
    public void legitimateInlineStyleIsPreserved() throws Exception {
        for (int mode : MODES) {
            String out = scan("<div style=\"color:red\">x</div>", mode).toLowerCase();
            assertTrue(modeName(mode) + " dropped the style attribute: " + out, out.contains("style="));
            assertTrue(modeName(mode) + " dropped a colour declaration: " + out, out.contains("color"));
            assertTrue(modeName(mode) + " dropped the colour value: " + out, out.contains("red"));
        }
    }
}
