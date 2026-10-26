package bench.antisamy;

import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/** The policy's ordinary denials keep working. */
public class FunctionalBaselineTest extends Base {

    @Test
    public void scriptAndEventHandlersAreStillRemoved() throws Exception {
        String input = "<script>alert(1)</script>"
                + "<img src=\"https://good.example/x.png\" onerror=\"alert(1)\">";
        for (int mode : MODES) {
            String out = scan(input, mode).toLowerCase();
            assertFalse(modeName(mode) + " kept a script element: " + out, out.contains("<script"));
            assertFalse(modeName(mode) + " kept an event handler: " + out,
                    java.util.regex.Pattern.compile("\\bon[a-z]{3,}\\s*=").matcher(out).find());
            assertTrue(modeName(mode) + " dropped an approved image: " + out, out.contains("good.example/x.png"));
        }
    }
}
