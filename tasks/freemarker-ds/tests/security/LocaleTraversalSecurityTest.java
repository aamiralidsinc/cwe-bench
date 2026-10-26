package verifier.security;

import freemarker.template.Configuration;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.util.Locale;

/**
 * A locale whose parts carry path separators must not make a lookup leave the template root, whichever public
 * way the locale is delivered to the engine.
 */
public class LocaleTraversalSecurityTest {

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
    public void variantPartWithPathSeparators() {
        sandbox.assertBlocked(sandbox.config(), "t.ftl", new Locale("en", "US", "sub/../../secret"), null);
    }

    @Test
    public void languagePartWithPathSeparators() {
        sandbox.assertBlocked(sandbox.config(), "t.ftl", new Locale("sub/../../secret"), null);
    }

    @Test
    public void countryPartWithPathSeparators() {
        sandbox.assertBlocked(sandbox.config(), "t.ftl", new Locale("en", "sub/../../secret"), null);
    }

    @Test
    public void localeUsedAsTheConfigurationDefault() throws Exception {
        Configuration cfg = sandbox.config();
        cfg.setLocale(new Locale("en", "US", "sub/../../secret"));
        sandbox.assertDefaultLocaleBlocked(cfg, "t.ftl");
    }

    @Test
    public void localeSetFromInsideATemplate() {
        sandbox.assertBlocked(sandbox.config(), "main.ftl", new Locale("en", "US"), null);
    }

}
