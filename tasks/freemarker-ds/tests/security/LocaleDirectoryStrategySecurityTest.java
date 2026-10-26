package verifier.security;

import freemarker.cache.LocaleDirectoryTemplateLookupStrategy;
import freemarker.template.Configuration;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.util.Locale;

/**
 * The locale-directory lookup convention must not turn locale parts into path steps any more than the default
 * locale-infix convention does.
 */
public class LocaleDirectoryStrategySecurityTest {

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
    public void directoryLocaleVariantWithPathSeparators() {
        Configuration cfg = sandbox.config();
        cfg.setTemplateLookupStrategy(LocaleDirectoryTemplateLookupStrategy.INSTANCE);
        sandbox.assertBlocked(cfg, "t.ftl", new Locale("en", "US", "sub/../.."), null);
    }

}
