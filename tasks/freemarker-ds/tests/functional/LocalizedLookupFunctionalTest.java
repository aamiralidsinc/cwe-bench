package verifier.functional;

import freemarker.template.Configuration;
import freemarker.template.Template;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.StringWriter;
import java.util.HashMap;
import java.util.Locale;

import static org.junit.Assert.assertEquals;

/** Localized template selection keeps its exact name format and fallback order. */
public class LocalizedLookupFunctionalTest {

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
    public void mostSpecificLocaleWins() throws Exception {
        assertResolved(sandbox.config("/tpl/"), "t.ftl", new Locale("en", "US"),
                "t_en_US.ftl", "EN-US");
    }

    @Test
    public void fallsBackToLanguage() throws Exception {
        assertResolved(sandbox.config("/tpl/"), "t.ftl", new Locale("en", "GB"),
                "t_en.ftl", "EN");
    }

    @Test
    public void fallsBackToUnlocalizedName() throws Exception {
        assertResolved(sandbox.config("/tpl/"), "t.ftl", Locale.FRENCH,
                "t.ftl", "BASE");
    }

    @Test
    public void variantLocaleUsesTheVariantInfix() throws Exception {
        assertResolved(sandbox.config("/tpl/"), "t.ftl", new Locale("en", "US", "VAR"),
                "t_en_US_VAR.ftl", "EN-US-VAR");
    }

    @Test
    public void scriptLocaleUsesTheHashScriptInfix() throws Exception {
        Locale locale = new Locale.Builder().setLanguage("en").setRegion("US").setScript("Latn").build();
        assertResolved(sandbox.config("/tpl/"), "t.ftl", locale, "t_en_US_#Latn.ftl", "EN-US-LATN");
    }

    @Test
    public void variantFallsBackToLessSpecificLocale() throws Exception {
        FunctionalSandbox extra = new FunctionalSandbox();
        try {
            // This sandbox has no t_en_US_OTHER.ftl; the variant must be dropped and t_en_US.ftl used.
            assertResolved(extra.config("/tpl/"), "t.ftl", new Locale("en", "US", "OTHER"),
                    "t_en_US.ftl", "EN-US");
        } finally {
            extra.classPath.close();
        }
    }

    @Test
    public void localizedLookupCanBeDisabled() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        cfg.setLocalizedLookup(false);
        assertResolved(cfg, "t.ftl", new Locale("en", "US"), "t.ftl", "BASE");
    }

    @Test
    public void configurationDefaultLocaleIsUsed() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        cfg.setLocale(new Locale("en", "US"));
        Template template = cfg.getTemplate("t.ftl");
        assertEquals("t_en_US.ftl", template.getSourceName());
        assertEquals("EN-US", render(template));
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
