package bench.antisamy;

import org.junit.Test;

import static org.junit.Assert.assertFalse;

/**
 * An element that a browser treats as a container must not be returned open, or everything the
 * page renders after the client's fragment would become part of it.
 */
public class SecurityElementBoundaryTest extends Base {

    @Test
    public void emptyContainerElementIsNotSelfClosed() throws Exception {
        String input = "<div></div>after";
        for (int mode : MODES) {
            String out = scan(input, mode);
            assertFalse(modeName(mode) + " returned an open container: " + out, isSelfClosed(out, "div"));
        }
    }

    @Test
    public void emptyTextAreaIsNotSelfClosed() throws Exception {
        String input = "<textarea></textarea>after";
        for (int mode : MODES) {
            String out = scan(input, mode);
            assertFalse(modeName(mode) + " returned an open text area: " + out, isSelfClosed(out, "textarea"));
        }
    }

    @Test
    public void emptyObjectIsNotSelfClosed() throws Exception {
        String input = "<object></object>after";
        for (int mode : MODES) {
            String out = scan(input, mode);
            assertFalse(modeName(mode) + " returned an open object: " + out, isSelfClosed(out, "object"));
        }
    }
}
