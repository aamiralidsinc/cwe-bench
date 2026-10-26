package bench.antisamy;

import org.junit.Test;

/** Text that a style element carries must never reach the output as markup. */
public class SecurityStyleContentTest extends Base {

    @Test
    public void advisoryCdataSmugglingIsNotEmitted() throws Exception {
        String input = "<style/>b<![cdata[</style><a href=javascript:alert(1)>test";
        for (int mode : MODES) {
            assertNoExecutableContent("style cdata over " + modeName(mode), scan(input, mode));
        }
    }

    @Test
    public void selectStyleSmugglingIsNotEmitted() throws Exception {
        String input = "<select<style/>W<xmp<script>alert(1)</script>";
        for (int mode : MODES) {
            assertNoExecutableContent("select/style over " + modeName(mode), scan(input, mode));
        }
    }

    @Test
    public void focusHandlerSmuggledIntoStyleIsNotEmitted() throws Exception {
        String input = "<select<style/>k<input<</>input/onfocus=alert(1)>";
        for (int mode : MODES) {
            assertNoExecutableContent("multi-node style over " + modeName(mode), scan(input, mode));
        }
    }
}
