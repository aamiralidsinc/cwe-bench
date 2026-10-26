package bench.antisamy;

import org.junit.Test;

import static org.junit.Assert.assertTrue;

/** Serialisation keeps the forms the product already promises. */
public class FunctionalSerializationTest extends Base {

    @Test
    public void voidElementsKeepTheirSelfClosingForm() throws Exception {
        String input = "<br><img src=\"https://good.example/x.png\"><hr><input type=\"text\">";
        for (int mode : MODES) {
            String out = scan(input, mode);
            assertTrue(modeName(mode) + " changed a line break: " + out,
                    out.matches("(?is).*<br\\s*/>.*"));
            assertTrue(modeName(mode) + " changed an image: " + out,
                    out.matches("(?is).*<img\\b[^>]*?/>.*"));
            assertTrue(modeName(mode) + " changed a rule: " + out,
                    out.matches("(?is).*<hr\\s*/>.*"));
            assertTrue(modeName(mode) + " changed an input: " + out,
                    out.matches("(?is).*<input\\b[^>]*?/>.*"));
        }
    }

    @Test
    public void emptyContainerIsStillReturned() throws Exception {
        String input = "<div></div>after";
        for (int mode : MODES) {
            String out = scan(input, mode);
            assertTrue(modeName(mode) + " dropped an approved empty container: " + out, out.contains("<div"));
            assertTrue(modeName(mode) + " dropped following content: " + out, out.contains("after"));
        }
    }
}
