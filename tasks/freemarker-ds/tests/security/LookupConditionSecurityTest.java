package verifier.security;

import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.util.Locale;

/**
 * The other lookup parameter a caller can supply must not be able to address a template source outside the
 * template root either, and an included template must not become a way around it.
 */
public class LookupConditionSecurityTest {

    private static Sandbox sandbox;

    @BeforeClass
    public static void setUp() throws Exception {
        sandbox = new Sandbox();
    }

    @AfterClass
    public static void tearDown() throws Exception {
        if (sandbox != null) {
            sandbox.classPath.close();
        }
    }

    @Test
    public void conditionValueWithPathSeparators() {
        sandbox.assertBlocked(sandbox.config(), "t.ftl", Locale.FRENCH, "sub/../..");
    }

    @Test
    public void includedTemplateUsesTheSameCondition() {
        sandbox.assertBlocked(sandbox.config(), "include.ftl", Locale.FRENCH, "sub/../..");
    }

}
