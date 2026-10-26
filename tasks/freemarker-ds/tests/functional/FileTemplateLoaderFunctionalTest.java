package verifier.functional;

import freemarker.cache.FileTemplateLoader;
import freemarker.template.Configuration;
import freemarker.template.Template;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.StringWriter;
import java.util.HashMap;
import java.util.Locale;

import static org.junit.Assert.assertEquals;

/** The file-system template loader keeps its localized lookup and containment behaviour. */
public class FileTemplateLoaderFunctionalTest {

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
    public void localizedLookupWorksOnTheFileSystem() throws Exception {
        assertResolved(new Locale("en", "US"), "EN-US");
    }

    @Test
    public void languageFallbackWorksOnTheFileSystem() throws Exception {
        assertResolved(new Locale("en", "GB"), "EN");
    }

    @Test
    public void baseTemplateWorksOnTheFileSystem() throws Exception {
        assertResolved(Locale.FRENCH, "BASE");
    }

    private static void assertResolved(Locale locale, String expectedOutput)
            throws Exception {
        Configuration cfg = new Configuration(Configuration.VERSION_2_3_32);
        cfg.setTemplateLoader(new FileTemplateLoader(sandbox.tpl.toFile()));
        cfg.setLocalizedLookup(true);
        cfg.setDefaultEncoding("UTF-8");
        cfg.setLocale(Locale.US);
        Template template = cfg.getTemplate("t.ftl", locale);
        StringWriter out = new StringWriter();
        template.process(new HashMap<String, Object>(), out);
        assertEquals(expectedOutput, out.toString());
    }

}
