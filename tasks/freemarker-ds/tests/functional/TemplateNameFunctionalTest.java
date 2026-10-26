package verifier.functional;

import freemarker.template.Configuration;
import freemarker.template.Template;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.util.Locale;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;

/** Requested template names keep being normalized and rejected exactly as before. */
public class TemplateNameFunctionalTest {

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
    public void nameBackingOutOfTheRootIsRejected() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        assertNull(cfg.getTemplate("../ok.ftl", null, null, null, true, true));
    }

    @Test
    public void plainNameStillLoads() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        Template template = cfg.getTemplate("t.ftl", Locale.FRENCH);
        assertEquals("t.ftl", template.getSourceName());
    }

    @Test
    public void nestedNameStillLoads() throws Exception {
        Configuration cfg = sandbox.config("/tpl/");
        Template template = cfg.getTemplate("dark/t.ftl", Locale.FRENCH);
        assertEquals("dark/t.ftl", template.getSourceName());
    }

}
