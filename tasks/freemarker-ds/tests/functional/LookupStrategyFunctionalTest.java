package verifier.functional;

import freemarker.cache.LocaleDirectoryTemplateLookupStrategy;
import freemarker.template.Configuration;
import freemarker.template.Template;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.StringWriter;
import java.util.HashMap;
import java.util.Locale;

import static org.junit.Assert.assertEquals;

/** The alternate lookup conventions keep resolving legitimate templates inside the template root. */
public class LookupStrategyFunctionalTest {

    private static FunctionalSandbox sandbox;

    @BeforeClass
    public static void setUp() throws Exception {
        sandbox = new FunctionalSandbox();
    }

    @AfterClass
    public static void tearDown() throws Exception {
        if (sandbox != null) {
            sandbox.classPath.close();
        }
    }

    @Test
    public void localeDirectoryMostSpecific() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        cfg.setTemplateLookupStrategy(LocaleDirectoryTemplateLookupStrategy.INSTANCE);
        assertResolved(cfg, "t.ftl", new Locale("en", "US"), "en_US/t.ftl", "DIR-EN-US");
    }

    @Test
    public void localeDirectoryFallsBackToLanguage() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        cfg.setTemplateLookupStrategy(LocaleDirectoryTemplateLookupStrategy.INSTANCE);
        assertResolved(cfg, "t.ftl", new Locale("en", "GB"), "en/t.ftl", "DIR-EN");
    }

    @Test
    public void localeDirectoryFallsBackToRoot() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        cfg.setTemplateLookupStrategy(LocaleDirectoryTemplateLookupStrategy.INSTANCE);
        assertResolved(cfg, "t.ftl", Locale.FRENCH, "t.ftl", "BASE");
    }

    @Test
    public void localeDirectoryVariantFallsBack() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        cfg.setTemplateLookupStrategy(LocaleDirectoryTemplateLookupStrategy.INSTANCE);
        assertResolved(cfg, "t.ftl", new Locale("en", "US", "OTHER"), "en_US/t.ftl", "DIR-EN-US");
    }

    @Test
    public void conditionDirectoryOverridesTemplate() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        Template template = cfg.getTemplate("t.ftl", Locale.FRENCH, "dark", "UTF-8", true, false);
        assertEquals("dark/t.ftl", template.getSourceName());
        assertEquals("DARK", render(template));
        assertEquals("dark", template.getCustomLookupCondition());
    }

    @Test
    public void missingConditionDirectoryFallsThrough() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        Template template = cfg.getTemplate("t.ftl", Locale.FRENCH, "nosuch", "UTF-8", true, false);
        assertEquals("t.ftl", template.getSourceName());
        assertEquals("BASE", render(template));
    }

    @Test
    public void includedTemplateUsesConditionDirectory() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        Template template = cfg.getTemplate("main.ftl", Locale.FRENCH, "dark", "UTF-8", true, false);
        assertEquals("main.ftl", template.getSourceName());
        assertEquals("DARK-I", render(template));
    }

    private static void assertResolved(Configuration cfg, String name, Locale locale,
            String expectedSourceName, String expectedOutput) throws Exception {
        Template template = cfg.getTemplate(name, locale);
        assertEquals(expectedSourceName, template.getSourceName());
        assertEquals(expectedOutput, render(template));
    }

    private static String render(Template template) throws Exception {
        StringWriter out = new StringWriter();
        template.process(new HashMap<String, Object>(), out);
        return out.toString();
    }

}
